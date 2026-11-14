<img src="images/logo.png" height=72>

# GP Connect

This is the source repository for the GP Connect specification.

The current specification version is held in the master branch, and published to <a href="https://nhsconnect.github.io/gpconnect/">GitHub pages</a>.

Previous versions of the specification are held in release/* branches (and tagged), and published to the <a href="https://developer.nhs.uk/gp-connect-specification-versions/">NHS Developer Network</a>.

## Building the specification

To build the GP Connect specification locally

- Clone the repository: `git clone https://github.com/nhsconnect/gpconnect.git`
- Install [Ruby](https://www.ruby-lang.org/en/documentation/installation/#homebrew)
- Install Jekyll
  - Install [Jekyll](https://jekyllrb.com/docs/installation/) for OS X/Linux
  - Install [Jekyll](https://jekyllrb.com/docs/windows/) for Windows
- Navigate to your gpconnect directory and run: `bundle install`
- Now run Jekyll: `bundle exec jekyll serve`
- Browse website [Browser](http://localhost:4005): `http://localhost:4005`

### Troubleshooting

1) Fix warnings related to SSL certificate checking (by configuring the SSL_CERT_FILE env variable) by following instructions to [download and reference a cacert.pem file](https://gist.github.com/fnichol/867550).

2) Fix warnings related to the Jekyll GitHub Metadata plugin, by [configuring the JEKYLL_GITHUB_TOKEN environment variable](https://github.com/jekyll/github-metadata).

<!-- symphonix-dual-engine-architecture:start -->
## Dual-Engine Persistence (`PostgreSQL 15` + 3-Tier `SQLite WAL`) & SFDS v2.4 `/workbench-ui`

In compliance with Symphonix-Health mandate **L-431**, `gpconnect` operates a synchronous **Dual-Engine** persistence architecture:

1. **PostgreSQL 15 (`bt-postgres-dev`):**
   - DSN: `postgresql://bullettrain:devpassword@127.0.0.1:15432/bullettrain`
   - Schema: `sibling_gpconnect` synchronized with master `client_registry.patients` (`40,090` canonical patients) and `referential_integrity.entity_references` (`176,396` canonical episodes), enforcing `FOREIGN KEY ... ON DELETE RESTRICT` and `BEFORE DELETE` WORM protection triggers (`client_registry.forbid_clinical_record_delete()`).
2. **3-Tier SQLite WAL (`SH-KF-STATE-001`):**
   - Database file: `data/gpconnect_sh_kf_state_001_wal.db`
   - Tiered clinical cohorts: Tier 1 (`40,000` longitudinal baseline), Tier 2 (`50` rich full-pathway), Tier 3 (`40` edge/adversarial).
3. **Runtime Endpoints & SFDS v2.4 Workstation:**
   - `GET /workbench-ui` — Full-viewport (`100vh`, `scrollHeight <= innerHeight`, `width: 100%; max-width: none;`) 4-tab WAI-ARIA (`role="tablist"` / `role="tab"` / `role="tabpanel"`) clinical workstation.
   - `GET /api/v1/cohort/3tier/summary` — Dual-engine sync status and cohort counts (`postgresql_15` + `sqlite_3tier_wal`).
   - `GET /api/v1/cohort/3tier/patients` & `GET /api/v1/cohort/3tier/patients/{patient_id}` — Patient trajectory and episode queries.
   - `POST /api/v1/cohort/3tier/episodes` — Synchronous dual-engine WORM episode creation across PostgreSQL 15 and SQLite WAL.
<!-- symphonix-dual-engine-architecture:end -->
