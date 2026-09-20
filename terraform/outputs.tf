output "cloud_run_service_url" {
  description = "The deployed Cloud Run URL to configure in GECX Agent Studio."
  value       = google_cloud_run_v2_service.geap_backend.uri
}

output "service_account_email" {
  description = "Service account running the GEAP backend microservice."
  value       = google_service_account.geap_sa.email
}

output "secret_manager_secret_id" {
  description = "Secret Manager secret ID containing the APEX_AUTH_TOKEN."
  value       = google_secret_manager_secret.auth_token_secret.id
}
