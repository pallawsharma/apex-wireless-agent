# Infrastructure as Code (IaC) for Apex Wireless Hybrid GEAP Backend
# Provisions Google Cloud Run, Secret Manager, and IAM permissions.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Google Cloud Service APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "texttospeech.googleapis.com",
  ])

  service            = each.key
  disable_on_destroy = false
}

# 2. Secret Manager: Store Enterprise Authentication Token
resource "google_secret_manager_secret" "auth_token_secret" {
  secret_id = "apex-auth-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "auth_token_version" {
  secret      = google_secret_manager_secret.auth_token_secret.id
  secret_data = var.apex_auth_token
}

# 3. Dedicated Service Account for GEAP Backend
resource "google_service_account" "geap_sa" {
  account_id   = "apex-geap-runner"
  display_name = "Apex Wireless GEAP Backend Runner"
}

# Grant Vertex AI User role to the Service Account
resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.geap_sa.email}"
}

# Grant Secret Accessor role to the Service Account
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.auth_token_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.geap_sa.email}"
}

# 4. Google Cloud Run (v2) Microservice Deployment
resource "google_cloud_run_v2_service" "geap_backend" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.geap_sa.email

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      ports {
        container_port = 8080
      }

      env {
        name  = "PORT"
        value = "8080"
      }
      env {
        name  = "PYTHONUNBUFFERED"
        value = "1"
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "1"
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "APEX_ENFORCE_AUTH"
        value = "1"
      }

      # Inject secret directly from Secret Manager
      env {
        name = "APEX_AUTH_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.auth_token_secret.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/healthz"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 10
      }

      liveness_probe {
        http_get {
          path = "/healthz"
          port = 8080
        }
        period_seconds = 15
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
  }

  depends_on = [
    google_project_service.services,
    google_secret_manager_secret_version.auth_token_version,
  ]
}

# 5. Public Invoker IAM policy (allows GECX Webhook to reach Cloud Run)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  location = google_cloud_run_v2_service.geap_backend.location
  name     = google_cloud_run_v2_service.geap_backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
