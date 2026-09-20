variable "project_id" {
  description = "The Google Cloud Project ID to deploy resources to."
  type        = string
  default     = "google.com:nextgen-sandbox"
}

variable "region" {
  description = "The Google Cloud region for Cloud Run and Secret Manager."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run microservice."
  type        = string
  default     = "apex-geap-backend"
}

variable "container_image" {
  description = "Artifact Registry container image URI for the GEAP backend."
  type        = string
  default     = "us-central1-docker.pkg.dev/google.com:nextgen-sandbox/apex-wireless/geap-backend:latest"
}

variable "apex_auth_token" {
  description = "The enterprise secret authorization token for GECX -> GEAP calls."
  type        = string
  sensitive   = true
  default     = "apex-enterprise-secret-token-2026"
}
