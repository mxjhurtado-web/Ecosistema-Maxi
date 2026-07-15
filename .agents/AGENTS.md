# Ecosistema-Maxi Workspace Configuration & Memory

## GCP Integration Details
* **Project Name in GCP:** `Ecosistema Orbi` (formerly `MaxiBot`)
* **Project ID in GCP:** `maxibot-472423`
* **Google Chat Bot Name:** `@ ORBIT Middleware Bot` (or renamed equivalent in `Ecosistema Orbi`)
* **Service Account Email:** `maxibot-sa@maxibot-472423.iam.gserviceaccount.com`
* **SA Credentials Location:** Configured via Base64 string of JSON key in env `GOOGLE_CHATS_SA_BASE64` or Redis key `config:google_chat_alert`.
* **Google Sheets Integrations:**
  * **FAQ Knowledge Base Sheet ID:** `1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE` (tab `Contenido` or first tab)
  * **Reglas Sheet ID:** `1eFm3L_ALVr78wTDBB2bsg7Wq6DT9ZoGzIX9tKLN9nGw`
  * **Scripts Sheet ID:** `18VE3tdVt4E-eNrf0dD4zlk1aLV2nfv9_ncdUvLPaNic`
  * **Estatus Sheet ID:** `14BdjBuXPXPkjXMKS-955fA6bNw5qRMv5IWCNhMZGIXc`
  * **Bill Estatus Sheet ID:** `16fB_MGtha0NUtp5mge7UwvHcWo1NYVnOGVv6Yntv9xo`
  * **Topup Estatus Sheet ID:** `1E3pNthg7myh7tgjEnb_TIxCnTLFi_gzWlcxk2LOdNCs`

## Future Architecture Plan: Dedicated "Maxibot" Agent
* **Objective:** Isolate the conversational agent "Maxibot" from the main middleware.
* **Credentials:** Maxibot will have its own **separate, dedicated Service Account** (distinct from `maxibot-sa`).
* **Permissions/Scope:** This new Service Account will exclusively have access to:
  1. The FAQ Knowledge Base Google Sheet: `1wrtj7SZ6wB9h1yd_9h613DYNPGjI69_Zj1gLigiUHtE`.
  2. A new, custom MCP server (to be configured in the future).
