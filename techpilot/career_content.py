"""Career-specific learning content shared by TechPilot learning pages."""

CAREER_CHOICES = [
    "Cloud Engineer",
    "Data Analyst",
    "Full Stack Developer",
    "AI/ML Engineer",
    "Android Developer",
    "Cybersecurity Analyst",
    "Not Sure Yet",
]

CAREER_SKILLS = {
    "Cloud Engineer": ["Linux", "Networking", "AWS", "Azure", "Docker", "Kubernetes", "IAM", "CI/CD", "Monitoring", "Terraform"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Django", "REST APIs", "Git", "SQL", "Testing"],
    "Data Analyst": ["SQL", "Excel", "Python", "Pandas", "NumPy", "Statistics", "Data Visualization", "Power BI", "Tableau"],
    "AI/ML Engineer": ["Python", "NumPy", "Pandas", "Statistics", "Linear Algebra", "Machine Learning", "Scikit-learn", "Deep Learning", "TensorFlow", "Model Evaluation"],
    "Android Developer": ["Kotlin", "Java", "Android Studio", "Android SDK", "Activities", "Intents", "Jetpack Compose", "Room", "APIs", "Testing"],
    "Cybersecurity Analyst": ["Networking", "Linux", "Python", "Security Fundamentals", "OWASP Top 10", "Web Security", "Burp Suite", "Nmap", "Wireshark", "Vulnerability Assessment"],
    "Not Sure Yet": ["Python", "SQL", "Git", "Problem Solving", "Communication", "Career Exploration"],
}

# level, title, problem, objective, stack, skills, estimated time, activity, stretch
PROJECT_SPECS = {
    "Cloud Engineer": [
        ("Beginner", "Static site on object storage", "A small organization needs a low-cost public information page.", "Publish a static site with safe public-read access limited to the site assets.", "AWS S3, HTML, IAM", "Object storage, IAM, DNS basics", "4–6 hours", "Configure a bucket, upload versioned assets, and verify access with a least-privilege policy.", "Add a CDN and HTTPS with a documented cache invalidation."),
        ("Beginner", "Linux server setup checklist", "A new VM needs a repeatable and secure first-day setup.", "Create a documented setup script and verification checklist.", "Linux, Bash, SSH", "Linux, shell scripting, access control", "3–5 hours", "Create a non-root account, configure SSH safely, apply updates, and test each checklist item.", "Make the script idempotent and log its actions."),
        ("Beginner", "Cloud cost estimator", "A team cannot explain which planned resources drive its monthly estimate.", "Build a small calculator that records assumptions and estimated totals.", "Python, CSV, cloud pricing inputs", "Python, cost awareness, documentation", "4–6 hours", "Define input assumptions, calculate monthly totals, validate edge cases, and document limitations.", "Compare two deployment sizes and produce a cost summary."),
        ("Beginner", "Private file backup workflow", "A developer needs a repeatable backup of sample project files.", "Back up owned sample files and verify restoration.", "AWS CLI, S3, Bash", "CLI, storage, backup verification", "4–6 hours", "Create a test dataset, upload it to a private bucket, list versions, and restore into a new folder.", "Add a scheduled dry-run report."),
        ("Beginner", "Cloud resource inventory", "A learner needs a clear inventory of resources in a sandbox account.", "Generate a tagged inventory report for an authorized training account.", "AWS CLI, Python, JSON", "Resource inventory, tags, scripting", "4–6 hours", "Use read-only commands, normalize resource metadata, and export a report with account and region context.", "Flag untagged sandbox resources for review."),
        ("Intermediate", "EC2 web app deployment", "A small app needs a documented single-instance deployment for a learning environment.", "Deploy an app to a restricted test VM with repeatable setup steps.", "AWS EC2, Linux, Nginx, Git", "Compute, networking, deployment", "1–2 days", "Create a least-privilege security group, configure the VM, deploy the app, and verify health checks.", "Automate deployment with a CI pipeline."),
        ("Intermediate", "Cloud monitoring and alerting", "A service owner cannot tell when a test service becomes unavailable.", "Collect service metrics and send a threshold alert in a sandbox.", "CloudWatch, EC2, SNS", "Metrics, alert thresholds, operations", "1–2 days", "Choose actionable metrics, create an alarm, trigger a controlled test condition, and record the response.", "Add a runbook link and a second symptom-based alarm."),
        ("Intermediate", "Containerized service pipeline", "A team wants consistent builds between a laptop and a test host.", "Build and publish a container image through a simple CI pipeline.", "Docker, GitHub Actions, Linux", "Containers, CI/CD, image hygiene", "2–3 days", "Write a small Dockerfile, run tests in CI, scan configuration, and publish to a private test registry.", "Add image signing and a rollback workflow."),
        ("Advanced", "Multi-tier resilient deployment", "A growing app needs separated network tiers and a documented recovery path.", "Design and deploy a small resilient architecture in a sandbox account.", "AWS VPC, ALB, EC2, RDS, IaC", "Network design, resilience, infrastructure as code", "1–2 weeks", "Define threat and availability assumptions, build private tiers, add health checks, and rehearse recovery.", "Add a staged deployment and measured recovery objective."),
        ("Advanced", "Policy-based cloud governance", "A training team needs guardrails that prevent risky sandbox configurations.", "Implement and test policy checks for a small set of approved resources.", "Terraform, OPA, CI", "Policy as code, governance, automated testing", "1–2 weeks", "Write policy rules, create compliant and non-compliant fixtures, integrate checks into CI, and document exceptions.", "Add drift detection and a review report."),
    ],
    "Data Analyst": [
        ("Beginner", "Sales spreadsheet cleanup", "A sales export contains inconsistent dates, blanks, and duplicate rows.", "Create a repeatable cleaning workflow and a quality summary.", "Excel or Google Sheets", "Data cleaning, formulas, quality checks", "3–5 hours", "Profile columns, standardize dates, handle duplicates, document assumptions, and compare row counts.", "Automate checks with a spreadsheet validation tab."),
        ("Beginner", "SQL store performance report", "A store owner wants a simple view of sales by product.", "Write queries that summarize a small sample sales database.", "SQLite, SQL", "SELECT, filtering, aggregation", "4–6 hours", "Create sample tables, write grouped queries, validate totals against source rows, and save the SQL.", "Add a date-range comparison."),
        ("Beginner", "Personal spending summary", "A learner wants to understand spending patterns from a sample transaction file.", "Produce a categorized monthly summary with transparent rules.", "Excel, CSV", "Categorization, pivot tables, charts", "3–5 hours", "Clean categories, build a pivot table, check uncategorized rows, and explain two patterns.", "Add a budget-versus-actual view."),
        ("Beginner", "Survey response snapshot", "A community group needs a concise summary of a small survey.", "Turn responses into a clear one-page summary.", "Sheets, charts", "Descriptive statistics, chart selection", "4–6 hours", "Check response counts, summarize categorical answers, chart results, and note sample limitations.", "Compare two respondent groups where sample size permits."),
        ("Beginner", "Simple KPI dashboard", "A small team tracks three operational measures manually.", "Create a dashboard with definitions and a refresh checklist.", "Excel, pivot tables", "KPI definitions, visualization, communication", "5–7 hours", "Define each metric, clean a sample dataset, create visuals, and test totals against the source.", "Add a dated refresh log and data quality indicators."),
        ("Intermediate", "Exploratory sales analysis", "A retailer needs to understand seasonal sales changes and product mix.", "Analyze a supplied or synthetic sales dataset and communicate evidence-based findings.", "Python, Pandas, Matplotlib", "EDA, grouping, interpretation", "1–2 days", "Inspect schema, handle missing values, compare periods, test outliers, and separate observations from causes.", "Add a reproducible notebook and sensitivity check."),
        ("Intermediate", "Interactive operations dashboard", "Managers need filters to explore service volume and wait time.", "Build an interactive dashboard with clear metric definitions.", "Power BI or Tableau, SQL", "Data modeling, visual design, filters", "2–3 days", "Model facts and dimensions, create measures, add useful filters, and validate totals with SQL.", "Add a refresh status and drill-through page."),
        ("Intermediate", "Customer retention cohort study", "A subscription team wants to compare retention across signup months.", "Create a cohort table and explain its limits.", "SQL, Python, Pandas", "Cohort analysis, date logic, business communication", "2–3 days", "Define cohort and active rules, calculate retention, test edge cases, and summarize findings.", "Compare cohorts by a carefully defined acquisition segment."),
        ("Advanced", "Forecasting with backtesting", "A planning team needs a baseline forecast with honest error measurements.", "Compare simple forecasting baselines using time-aware validation.", "Python, Pandas, Statsmodels", "Time series, leakage prevention, model evaluation", "1–2 weeks", "Establish a naive baseline, split chronologically, compare metrics, inspect residuals, and communicate uncertainty.", "Add prediction intervals and a monitoring threshold."),
        ("Advanced", "Analytics data mart", "Several reports use inconsistent definitions of revenue and customer.", "Build a tested analytical model with documented metric definitions.", "SQL, dbt, warehouse", "Dimensional modeling, testing, governance", "1–2 weeks", "Define grains, build staging and marts, add tests, reconcile totals, and document ownership.", "Add incremental loads with freshness checks."),
    ],
    "Full Stack Developer": [
        ("Beginner", "Responsive profile page", "A learner needs a polished page that works on phone and desktop.", "Build an accessible responsive profile with semantic structure.", "HTML, CSS", "Semantic HTML, layout, accessibility", "3–5 hours", "Sketch sections, build semantic markup, add responsive styles, test keyboard access, and check narrow screens.", "Add a theme toggle that respects system preferences."),
        ("Beginner", "JavaScript task tracker", "A user wants to add, complete, and remove tasks in one browser session.", "Create an interactive task list with clear empty and completed states.", "HTML, CSS, JavaScript", "DOM events, state, validation", "5–7 hours", "Define task state, build form validation, implement updates, and test empty and duplicate input.", "Persist tasks locally with a clear reset control."),
        ("Beginner", "Book catalog CRUD app", "A reader needs to track a small personal book collection.", "Build create, read, update, and delete screens backed by a local database.", "Python, Django, SQLite, HTML", "Django models, forms, CRUD", "1–2 days", "Model books, validate forms, add list and detail views, handle empty results, and test updates.", "Add search and pagination."),
        ("Beginner", "Recipe finder", "A household wants to search its own saved recipes by ingredient.", "Build a searchable recipe catalog with useful filters.", "Django, SQLite, CSS", "Query filtering, forms, templates", "1–2 days", "Define recipe fields, create sample data, implement search, escape user content, and test no-result behavior.", "Add a favorites list for authenticated users."),
        ("Beginner", "Personal notes app", "A user needs to create and organize short notes.", "Create a small notes application with clear ownership rules.", "Django, SQLite, Bootstrap", "Authentication, ownership, forms", "1–2 days", "Add note model, require login, scope queries to the owner, implement edit/delete, and test access boundaries.", "Add tags and a search view."),
        ("Intermediate", "Authenticated study planner", "Students need private tasks and due dates across sessions.", "Build a login-based planner with per-user data isolation.", "Django, PostgreSQL or SQLite, HTML", "Authentication, authorization, date handling", "2–3 days", "Design task states, scope all queries to the user, validate dates, add filters, and test cross-user denial.", "Add calendar export."),
        ("Intermediate", "REST API and React dashboard", "A team needs a client interface over a small project API.", "Build a paginated API and a responsive client dashboard.", "Django REST Framework, React, SQLite", "REST, client state, API errors", "3–5 days", "Define serializers and permissions, create API endpoints, handle loading/errors, and add integration tests.", "Add token-based API access with rotation guidance."),
        ("Intermediate", "Team issue board", "A small team needs a shared board with status and assignment.", "Build a permission-aware issue workflow.", "Django, JavaScript, PostgreSQL", "Relational modeling, permissions, workflow", "3–5 days", "Define roles and transitions, validate state changes server-side, add filters, and test unauthorized updates.", "Add audit history for state changes."),
        ("Advanced", "Scalable event booking service", "An event site must avoid overselling limited seats.", "Design and implement a transaction-safe booking flow.", "Django, PostgreSQL, Redis", "Transactions, concurrency, idempotency", "1–2 weeks", "Model inventory, use atomic reservations, enforce idempotency, load-test contention, and document failure recovery.", "Add an outbox for reliable confirmation events."),
        ("Advanced", "Production-ready SaaS workspace", "Multiple organizations need isolated projects and a dependable release process.", "Build a multi-tenant service with tests, observability, and deployment controls.", "Django, React, PostgreSQL, CI/CD", "Tenant isolation, observability, release engineering", "2–3 weeks", "Define tenant boundaries, test cross-tenant access, add structured logs, automate CI, and document rollback.", "Add background processing with retry-safe jobs."),
    ],
    "AI/ML Engineer": [
        ("Beginner", "Dataset quality notebook", "A tabular dataset has missing values and inconsistent categories.", "Create a reproducible data quality report before modeling.", "Python, Pandas, Jupyter", "Profiling, missing data, reproducibility", "4–6 hours", "Load data, inspect types, quantify missingness, clean with recorded rules, and compare before/after summaries.", "Add schema validation that fails on unexpected columns."),
        ("Beginner", "House price baseline model", "A learner needs a first regression model with an honest baseline.", "Train and evaluate a simple model without leaking the target.", "Python, Pandas, scikit-learn", "Features, train/test split, regression metrics", "1 day", "Define target, split data, build a baseline, inspect errors, and document limitations.", "Compare against a regularized model using cross-validation."),
        ("Beginner", "Customer churn classifier", "A sample subscription dataset needs a simple churn-risk baseline.", "Train a classifier and explain precision and recall trade-offs.", "Python, scikit-learn, Pandas", "Classification, class balance, evaluation", "1 day", "Check leakage, split data, train a baseline, inspect a confusion matrix, and explain threshold choices.", "Calibrate probabilities and compare thresholds."),
        ("Beginner", "Image classification starter", "A small labeled image set needs a reproducible classification experiment.", "Build a safe, small-scale baseline and document data limits.", "Python, TensorFlow or PyTorch", "Image preprocessing, validation, metrics", "1–2 days", "Inspect labels, create a split, normalize inputs, train a compact model, and inspect errors.", "Add augmentation and compare validation behavior."),
        ("Beginner", "Text sentiment explorer", "A sample review file needs a transparent sentiment baseline.", "Compare a simple text baseline with a clear error review.", "Python, scikit-learn, NLTK", "Text preprocessing, vectorization, evaluation", "1–2 days", "Clean text conservatively, split data, use TF-IDF, evaluate, and inspect misclassified examples.", "Compare a linear model with a keyword baseline."),
        ("Intermediate", "Feature engineering experiment", "A model's performance varies across sensible feature choices.", "Run a tracked experiment comparing domain-motivated features.", "Python, Pandas, scikit-learn", "Feature engineering, pipelines, experiment tracking", "2–3 days", "Set a baseline, build preprocessing pipelines, compare features with cross-validation, and record results.", "Add a reproducible experiment registry."),
        ("Intermediate", "Model error analysis toolkit", "A team needs to understand which examples its classifier gets wrong.", "Create slices and error summaries that guide the next experiment.", "Python, Pandas, scikit-learn", "Error analysis, slicing, responsible evaluation", "2–3 days", "Define useful slices, compare errors, inspect representative cases, and document limitations.", "Add drift-sensitive slice checks."),
        ("Intermediate", "Prediction API", "A validated model needs a small controlled inference interface.", "Serve a model with input validation and measurable health checks.", "FastAPI, scikit-learn, Docker", "Model serialization, API validation, monitoring", "3–4 days", "Package preprocessing with the model, validate schemas, add tests, containerize, and log safe metrics.", "Add versioned model endpoints and rollback."),
        ("Advanced", "Model monitoring and drift study", "Input patterns may shift after a model is deployed.", "Build a monitoring prototype that compares input and outcome indicators.", "Python, Evidently, Prometheus", "Drift, monitoring, alert design", "1–2 weeks", "Define reference data, calculate drift indicators, test known shifts, and set actionable alert thresholds.", "Add a retraining review gate rather than automatic retraining."),
        ("Advanced", "Responsible model release pipeline", "A team needs a repeatable review before promoting a model.", "Build a release pipeline with evaluation gates, provenance, and rollback.", "MLflow, Docker, CI/CD", "Model governance, reproducibility, deployment", "2–3 weeks", "Track data and model versions, enforce quality gates, record approvals, and rehearse rollback.", "Add a documented fairness review for relevant use cases."),
    ],
    "Android Developer": [
        ("Beginner", "Kotlin calculator", "A learner needs a small app to practice Kotlin expressions and input validation.", "Build a calculator screen with safe handling for invalid operations.", "Kotlin, Android Studio", "Kotlin functions, UI events, validation", "4–6 hours", "Sketch the screen, parse input safely, implement operations, handle divide-by-zero, and test cases.", "Add accessible history of recent calculations."),
        ("Beginner", "Profile card app", "A mobile profile needs a clean layout across common screen sizes.", "Create a responsive Android profile card.", "Kotlin, XML layouts or Compose", "Layouts, resources, accessibility", "4–6 hours", "Create reusable text and color resources, build layout, test long text, and verify accessibility labels.", "Add dark theme support."),
        ("Beginner", "Unit converter", "A learner wants quick conversions with clear units and validation.", "Build a simple converter with explicit input and output units.", "Kotlin, Compose", "State, input handling, formatting", "1 day", "Define supported conversions, validate values, implement state updates, and test boundary cases.", "Add conversion history stored locally."),
        ("Beginner", "Flashcard practice app", "A student wants to review a short set of study cards on a phone.", "Build a card deck with next, previous, and reveal actions.", "Kotlin, Compose", "State, navigation, UI testing", "1–2 days", "Model cards, implement navigation, add reveal behavior, and test empty and final-card states.", "Add simple spaced review dates."),
        ("Beginner", "Notes app with local storage", "A user needs notes to remain available after closing the app.", "Create a notes list backed by local persistence.", "Kotlin, Room", "Room, CRUD, lifecycle", "2 days", "Define an entity and DAO, build create/edit screens, handle empty state, and verify data after restart.", "Add search and export."),
        ("Intermediate", "Offline-first task app", "A learner needs tasks to remain usable without a network connection.", "Build a local-first task workflow with clear sync-ready boundaries.", "Kotlin, Room, ViewModel", "Architecture, persistence, testing", "3–5 days", "Separate UI and data layers, model task states, add repository tests, and verify process recreation.", "Add a mock sync queue with retry states."),
        ("Intermediate", "API-driven weather client", "A mobile screen needs to load a forecast and handle network failures clearly.", "Build an API client with loading, success, and error states.", "Kotlin, Retrofit, coroutines", "HTTP, async state, error handling", "3–5 days", "Define response models, keep secrets out of source, map errors, test loading states, and document API limits.", "Cache the last successful response locally."),
        ("Intermediate", "Photo gallery with paging", "A gallery should load image metadata in manageable pages.", "Build a responsive paged list with loading and retry states.", "Kotlin, Paging, Coil", "Paging, lifecycle, image loading", "4–6 days", "Create a paged source, show placeholders, handle failures, and test rotation and scrolling.", "Add offline metadata caching."),
        ("Advanced", "Secure account-based mobile client", "A mobile app needs authenticated API access and safe session handling.", "Build a client flow with secure token storage and clear sign-out behavior.", "Kotlin, Retrofit, Android Keystore", "Authentication, secure storage, threat modeling", "1–2 weeks", "Define token lifecycle, use platform-secure storage, handle expiry, test logout, and document sensitive-data handling.", "Add biometric unlock for local re-entry only."),
        ("Advanced", "Reliable background sync", "A mobile app must sync queued edits after connectivity returns.", "Implement conflict-aware background synchronization.", "Kotlin, Room, WorkManager", "Background work, idempotency, conflict resolution", "1–2 weeks", "Model a sync queue, use unique work, add retry/backoff, simulate conflicts, and expose sync status.", "Add telemetry that excludes personal content."),
    ],
    "Cybersecurity Analyst": [
        ("Beginner", "Security awareness lab", "A small team needs a safe way to recognize suspicious messages.", "Create a synthetic phishing-awareness exercise with no real credential collection.", "Local HTML, sample emails, checklist", "Phishing recognition, reporting, safe simulation", "3–5 hours", "Write fictional examples, annotate warning signs, provide a reporting path, and review accessibility.", "Add a short knowledge check using synthetic data only."),
        ("Beginner", "Personal device hardening checklist", "A learner wants a repeatable checklist for their own test device.", "Document baseline protections and verification steps.", "Operating system tools, checklist", "Updates, MFA, least privilege", "3–5 hours", "Inventory a device you own, enable updates and MFA, review permissions, and record verification evidence.", "Create a monthly review reminder."),
        ("Beginner", "Log review practice set", "A learner needs practice identifying normal and suspicious sample events.", "Annotate a fictional log dataset and explain escalation decisions.", "CSV, spreadsheet, sample logs", "Log fields, triage, evidence notes", "4–6 hours", "Use only supplied synthetic logs, group events, note uncertainty, and draft a concise escalation summary.", "Add a timeline and confidence labels."),
        ("Beginner", "Password policy explainer", "A club needs clear, practical account-security guidance.", "Create a short guide covering passphrases, MFA, and recovery.", "Markdown, diagrams", "Identity security, communication", "3–4 hours", "Research vendor-neutral guidance, explain trade-offs, review recovery risks, and test readability.", "Add a safe account recovery checklist."),
        ("Beginner", "Local security baseline report", "A learner needs to understand basic settings on a device they own.", "Produce a privacy-conscious baseline report without collecting secrets.", "Local system settings, Markdown", "Configuration review, documentation", "4–6 hours", "Choose a personally owned test device, check updates and firewall state, redact identifiers, and document findings.", "Compare the result to a public baseline checklist."),
        ("Intermediate", "Authorized web app assessment plan", "A team needs a scoped checklist before testing its own training application.", "Write a rules-of-engagement document and safe test plan for an owned lab.", "OWASP ASVS, local test app", "Scope, authorization, web security", "1–2 days", "Define written scope, test accounts, non-destructive checks, evidence handling, and stop conditions.", "Map checks to a remediation owner and retest plan."),
        ("Intermediate", "Vulnerability assessment report", "A lab owner needs findings that are reproducible and useful to developers.", "Report issues found in an intentionally vulnerable local training app only.", "OWASP Juice Shop local, Markdown", "Risk rating, evidence, remediation", "2–3 days", "Confirm lab authorization, reproduce within the lab, minimize evidence, describe impact, and provide mitigations.", "Add a retest section with verification criteria."),
        ("Intermediate", "Defensive alert triage workbook", "An analyst needs a consistent way to triage synthetic alert records.", "Build a decision log with severity, evidence, and escalation rationale.", "Synthetic SIEM export, spreadsheet", "Triage, prioritization, incident notes", "2–3 days", "Define severity criteria, group related events, record evidence links, and document false-positive handling.", "Add a measurable queue aging summary."),
        ("Advanced", "Detection engineering lab", "A defensive team needs a tested detection for a known benign simulation.", "Build and validate a detection using synthetic events in an isolated lab.", "Sigma, local SIEM, synthetic logs", "Detection logic, testing, false positives", "1–2 weeks", "Define the threat behavior, generate safe synthetic events, write a rule, test benign cases, and document tuning.", "Add versioned rule tests to CI."),
        ("Advanced", "Incident response tabletop", "A small organization wants to rehearse a ransomware response without using malware.", "Run a tabletop using a fictional scenario and produce an improvement plan.", "Facilitator guide, synthetic timeline", "Incident command, communication, recovery", "1–2 weeks", "Set roles, use a fictional inject timeline, record decisions, review evidence preservation, and assign follow-up owners.", "Repeat the exercise with a recovery-time objective."),
    ],
}


def projects_for_career(career):
    projects = []
    specs = PROJECT_SPECS.get(career, [])
    if career == "Not Sure Yet":
        specs = [
            ("Beginner", "Skills inventory", "A learner wants a clear picture of what they know and want to try.", "Record current skills, evidence, and interests without assigning a level.", "Notes, Git", "Reflection, Git", "1–2 hours", "List projects, coursework, and tasks you enjoyed; attach evidence and choose one topic to explore.", "Ask someone in a role you are curious about to review your inventory."),
            ("Beginner", "Career path comparison", "Several technology paths sound interesting.", "Compare daily work, entry skills, and learning preferences across two roles.", "Research, spreadsheet", "Research, communication", "2–3 hours", "Use role descriptions from multiple sources and record similarities, differences, and open questions.", "Conduct an informational interview and update your comparison."),
            ("Beginner", "Python or SQL starter exercise", "A learner wants to sample a practical technical task.", "Complete a small data task and reflect on the work style.", "Python or SQL", "Python, SQL, problem solving", "3–4 hours", "Use a public sample dataset, answer three questions, and document each step.", "Repeat the task in the other tool and compare the experience."),
            ("Beginner", "Web page exploration", "A learner wants to try building a visible result.", "Create and publish a simple accessible page.", "HTML, CSS, Git", "HTML, CSS, Git", "3–5 hours", "Build a small page, check it at phone width, and document what was enjoyable or difficult.", "Add a small JavaScript interaction."),
            ("Beginner", "Technology role journal", "A learner needs evidence to choose a next learning step.", "Track questions and observations while exploring a role.", "Notes, role descriptions", "Research, communication", "1–2 hours", "Review two role descriptions and record tools, tasks, and questions that remain unclear.", "Compare an entry-level and experienced role."),
            ("Intermediate", "Mini project sampler", "A learner wants to compare hands-on tasks from different paths.", "Complete one small task in two areas and reflect on fit.", "Python, HTML, Linux", "Problem solving, documentation", "1 day", "Choose two bounded tutorials, record setup time and challenges, and save the outputs.", "Ask a peer to review both outputs against the same criteria."),
            ("Intermediate", "Portfolio evidence audit", "A learner has work samples but no clear portfolio story.", "Organize work samples around skills and outcomes.", "Git, Markdown", "Git, documentation", "1 day", "Choose three examples, explain your contribution, and note what evidence supports each claim.", "Add a short demo or before-and-after explanation."),
            ("Intermediate", "Informational interview guide", "A learner wants to ask useful questions about a career.", "Prepare and conduct a respectful role exploration conversation.", "Research, notes", "Communication, research", "1 day", "Research the person's public role, prepare questions, request a short conversation, and record takeaways.", "Compare the takeaways with current job postings."),
            ("Advanced", "Career hypothesis portfolio", "A learner is choosing a specialization based on limited evidence.", "Test a career hypothesis with a scoped portfolio project.", "Git, chosen stack", "Planning, technical fundamentals", "1–2 weeks", "Select a role hypothesis, define a project that demonstrates two listed skills, and get feedback.", "Revise the project based on feedback and document the decision."),
            ("Advanced", "Personal learning plan", "A learner needs a sustainable next-quarter plan.", "Build a measurable plan based on evidence and constraints.", "Calendar, Git, learning resources", "Planning, reflection", "1 week", "Set one role target, select two skills, schedule practice, and define a review date.", "Review progress after two weeks and adjust based on actual time and interest."),
        ]
    for index, spec in enumerate(specs, start=1):
        level, title, problem, objective, stack, skills, duration, activity, stretch = spec
        projects.append({
            "key": f"{career}-{index}",
            "level": level,
            "title": title,
            "description": problem,
            "problem": problem,
            "objective": objective,
            "stack": stack,
            "skills": skills,
            "duration": duration,
            "steps": [
                f"Define acceptance criteria for: {problem}",
                f"Prepare the project environment with {stack}.",
                activity,
                "Test the expected and edge-case behavior; record the evidence.",
                f"Document the result and what you learned about {skills}.",
            ],
            "output": f"A working {title.lower()} project with setup notes, tests, and a short demonstration.",
            "stretch": stretch,
        })
    return projects


# Each career and level has two domain-specific technical prompts.
# Tuple: topic, prompt, evaluation, hint, key points, sample answer.
TECHNICAL_QUESTIONS = {
    "Cloud Engineer": {
        "Beginner": [
            ("Object storage", "How would you host a static website in object storage while limiting access to only the files the site needs?", "Checks storage basics and least-privilege thinking.", "Separate the website content from account-wide permissions.", "Bucket or container configuration; scoped read access; HTTPS; versioning and logging.", "I would use a dedicated bucket, grant only the required read access to site assets, keep administrative permissions private, enable HTTPS through a CDN, and test access from an unauthenticated browser."),
            ("Networking", "What is the difference between a subnet, route table, and security group in a cloud network?", "Checks core networking vocabulary.", "Describe where traffic is directed and where it is allowed.", "Subnet partitions address space; route table selects paths; security group filters resource traffic.", "A subnet is an address range in a network, a route table decides where traffic goes, and a security group allows or blocks traffic to supported resources."),
        ],
        "Intermediate": [
            ("Monitoring", "A web service has rising latency but no outage. Which signals would you inspect first and why?", "Checks operational diagnosis and signal selection.", "Compare user-facing symptoms with resource and dependency signals.", "Latency percentiles; error rate; saturation; dependency metrics; recent changes.", "I would compare p95/p99 latency and errors with CPU, memory, connection pools, and dependency timing, then correlate the change with deployments or traffic shifts before altering capacity."),
            ("Deployment", "How would you design a rollback-safe deployment for a small cloud service?", "Checks deployment safety and recovery planning.", "Think about health gates and compatibility between versions.", "Immutable artifact; health checks; staged rollout; database compatibility; rollback trigger.", "I would deploy a versioned artifact gradually, gate promotion on health metrics, keep schema changes backward compatible, and define an automatic or operator-triggered rollback before rollout begins."),
        ],
        "Advanced": [
            ("Resilience", "How would you assess whether a multi-tier service meets a stated availability target?", "Checks reliability engineering and measurable design.", "Work from dependencies, failure domains, and observed service-level indicators.", "SLI/SLO; dependency budget; failure domains; load and recovery tests; error budget.", "I would define user-visible SLIs, calculate dependency contributions, identify shared failure domains, and validate the design with load and recovery exercises against the SLO."),
            ("Governance", "How would you prevent risky infrastructure changes while keeping teams productive?", "Checks policy design and operational trade-offs.", "Use automated guardrails with an exception process.", "Policy as code; least privilege; CI checks; audit trail; time-bound exceptions.", "I would put high-confidence controls in policy-as-code and CI, provide approved reusable modules, log decisions, and use reviewed, time-bound exceptions for legitimate edge cases."),
        ],
    },
    "Data Analyst": {
        "Beginner": [
            ("SQL aggregation", "How would you calculate monthly revenue by product while avoiding duplicate counting after joining order items to customers?", "Checks relational reasoning and aggregation.", "Identify the grain of each table before joining.", "Define row grain; join keys; aggregate at the right grain; validate totals.", "I would confirm the grain of orders and line items, join on stable keys, aggregate line-item revenue once per product and month, and reconcile the total to the source system."),
            ("Data quality", "A spreadsheet has blank dates and duplicate transactions. How would you prepare it for analysis?", "Checks careful data cleaning.", "Keep raw data and make assumptions explicit.", "Preserve source; profile missingness; deduplicate by defined key; log row counts.", "I would preserve the raw file, profile missing values, agree on a transaction key, deduplicate only confirmed repeats, and record row counts and exclusions."),
        ],
        "Intermediate": [
            ("Dashboard design", "How would you design a dashboard for managers who need to investigate a fall in weekly sales?", "Checks metric definition and visual communication.", "Start from the decision the dashboard should support.", "Metric definition; trend and comparison; useful filters; data freshness; accessible visuals.", "I would define net sales and the comparison baseline, show a time trend and product or region breakdown, expose relevant filters, and display data freshness and caveats."),
            ("Cohort analysis", "How would you compare retention for signup cohorts with different ages?", "Checks cohort definitions and denominator choice.", "Compare like-for-like periods since signup.", "Cohort assignment; age-aligned periods; consistent active definition; censoring caveat.", "I would assign each user to a signup cohort, measure activity at the same elapsed month for each cohort, use a consistent active rule, and flag incomplete recent cohorts."),
        ],
        "Advanced": [
            ("Forecast evaluation", "How would you evaluate a demand forecast when the data has seasonal patterns and changing behavior?", "Checks validation design and uncertainty awareness.", "Avoid random splits for ordered observations.", "Rolling time splits; seasonal baseline; MAE or scaled metric; segment error; uncertainty.", "I would compare against a seasonal naive baseline using rolling-origin validation, inspect errors by horizon and segment, and communicate uncertainty and regime changes."),
            ("Analytics modeling", "Several teams report different customer counts. How would you create a trusted shared metric?", "Checks data modeling and governance.", "Clarify entity definition and table grain before writing a query.", "Business definition; grain; identity rules; tests; ownership and lineage.", "I would agree on the customer definition and identity rules, model at a documented grain, add uniqueness and relationship tests, reconcile results, and assign an owner for changes."),
        ],
    },
    "Full Stack Developer": {
        "Beginner": [
            ("HTTP and forms", "What happens from clicking a form submit button to seeing a response from a Django page?", "Checks request-response fundamentals.", "Walk through browser, URL, view, and template.", "HTTP method and payload; URL routing; validation; response rendering or redirect.", "The browser sends an HTTP request to the form action, Django routes it to a view, the view validates input and performs work, then returns a rendered response or redirect."),
            ("CRUD", "How would you validate a required field in a create form and show a useful error?", "Checks server-side validation basics.", "Client validation helps, but the server must enforce it.", "Server-side validation; preserve safe submitted values; clear field error; tests.", "I would validate in a Django form or view on the server, re-render the form with a field-specific message and safe values, and test both valid and invalid submissions."),
        ],
        "Intermediate": [
            ("Authorization", "How would you ensure users can edit only their own records in a CRUD application?", "Checks object-level access control.", "Apply ownership in the query as well as the interface.", "Filter by authenticated user; reject unauthorized IDs; protect POST; test cross-user access.", "I would scope the object lookup to both its ID and the authenticated user, enforce the same rule on every write endpoint, and test that another user's ID is denied."),
            ("API design", "How should a REST endpoint represent validation errors and a missing resource?", "Checks API conventions and client usability.", "Distinguish invalid input from a resource that does not exist.", "Appropriate status codes; stable error shape; field details; no sensitive internals.", "I would return a 4xx status appropriate to the condition, use a consistent JSON error structure with field details for validation, and avoid exposing stack traces or secrets."),
        ],
        "Advanced": [
            ("Concurrency", "How would you prevent two requests from booking the final available seat at the same time?", "Checks transaction and race-condition reasoning.", "Application-level checks alone can race.", "Atomic transaction; row lock or conditional update; uniqueness/invariant; idempotency.", "I would enforce the invariant in an atomic database operation, using a lock or conditional update and a database constraint where possible, then make retries idempotent."),
            ("Scalability", "A page becomes slow as the number of related records grows. How would you diagnose and improve it?", "Checks evidence-led performance work.", "Measure queries before changing architecture.", "Query count and plans; indexes; N+1; pagination; caching only after correctness.", "I would profile query count and latency, inspect the query plan, fix N+1 access with appropriate joins, add justified indexes, paginate, and measure again."),
        ],
    },
    "AI/ML Engineer": {
        "Beginner": [
            ("Train/test split", "Why should a test set stay separate from model selection and preprocessing decisions?", "Checks leakage awareness.", "The test set estimates performance on unseen data.", "Fit transforms on training data; avoid tuning on test; final unbiased estimate.", "If I repeatedly use test results to choose features or settings, the model indirectly learns from that set. I fit preprocessing on training data and reserve the test set for final evaluation."),
            ("Classification metrics", "When might accuracy be a poor metric for a classifier?", "Checks class imbalance and decision context.", "Consider the cost of false positives and false negatives.", "Class prevalence; precision and recall; confusion matrix; threshold trade-off.", "With rare positives, a model can be highly accurate by predicting the majority class. I would inspect precision, recall, the confusion matrix, and the cost of each error."),
        ],
        "Intermediate": [
            ("Feature pipelines", "How would you prevent preprocessing leakage in a cross-validation experiment?", "Checks pipeline-based evaluation.", "Every learned transform must be fit inside each training fold.", "Pipeline; fold-local fit; nested selection when tuning; reproducible split.", "I would put imputation, encoding, and scaling inside a pipeline passed to cross-validation so each transform is fit only on that fold's training portion."),
            ("Error analysis", "A model performs well overall but poorly for one important segment. What would you do next?", "Checks diagnostic and responsible evaluation.", "Verify sample size and data quality before changing the model.", "Define segment; confidence/sample size; error types; root-cause analysis; mitigation.", "I would validate the segment definition and sample size, inspect error types and data quality, assess impact, and test targeted mitigations without hiding the aggregate trade-off."),
        ],
        "Advanced": [
            ("Drift monitoring", "What signals would you monitor to decide whether a deployed model needs investigation?", "Checks monitoring beyond a single drift score.", "Combine input, service, and outcome signals.", "Input drift; performance when labels arrive; data quality; latency; alert thresholds.", "I would monitor schema and input distributions, latency and failure rates, and delayed outcome metrics when labels become available, with thresholds tied to investigation actions."),
            ("Release governance", "How would you make a model release reproducible and reversible?", "Checks end-to-end model operations.", "Track data, code, artifacts, evaluation, and serving configuration.", "Versioned artifacts; lineage; quality gates; staged rollout; rollback and audit.", "I would version data references, code, environment, and model artifact, enforce evaluation gates, stage rollout, capture approval, and keep a tested rollback path."),
        ],
    },
    "Android Developer": {
        "Beginner": [
            ("Activity lifecycle", "Why should an Android screen not rely only on a local variable to retain form state through rotation?", "Checks lifecycle awareness.", "The activity can be recreated.", "Configuration recreation; ViewModel or saved state; restore user input.", "Rotation can recreate the activity, so local variables may be lost. I would keep screen state in a ViewModel or saved-state mechanism and restore it after recreation."),
            ("Kotlin null safety", "How does Kotlin's nullable type system help prevent runtime null errors?", "Checks Kotlin fundamentals.", "Compare nullable and non-null types.", "Explicit nullable type; safe calls; Elvis/default; avoid force unwrap.", "A nullable type must be handled explicitly with safe calls or a fallback, while a non-null type guarantees a value by contract. I avoid force unwraps unless an invariant is proven."),
        ],
        "Intermediate": [
            ("Offline persistence", "How would you structure a notes screen so updates remain available after process recreation?", "Checks Android data-layer design.", "Persist data separately from transient UI state.", "Room entity and DAO; repository; ViewModel; loading and error states.", "I would persist notes in Room, expose data through a repository and ViewModel, and let the UI observe loading, success, and error state independent of the activity lifecycle."),
            ("Network errors", "How should an API-driven screen behave when a request times out or returns an error?", "Checks resilient mobile UX.", "Preserve useful state and give the user a recovery path.", "Loading state; timeout/error mapping; cached content; retry; no leaked details.", "I would map the error to a safe message, retain cached content if available, offer a retry action, and log diagnostic details without exposing secrets to the UI."),
        ],
        "Advanced": [
            ("Background sync", "How would you make queued background sync safe to retry after the app is killed?", "Checks durable work and idempotency.", "The operating system may stop or retry work.", "Persistent queue; unique work; idempotency key; bounded retries; conflict policy.", "I would persist operations before scheduling unique work, make server requests idempotent, use bounded backoff, and represent conflicts explicitly for reconciliation."),
            ("Mobile security", "How would you protect an authenticated mobile session and sensitive local data?", "Checks platform security judgment.", "Minimize stored secrets and use platform controls.", "Keystore-backed storage; TLS; token expiry; redacted logs; logout cleanup.", "I would keep tokens in Keystore-backed storage, use TLS, handle expiry and revocation, redact logs, and clear sensitive local state on sign-out."),
        ],
    },
    "Cybersecurity Analyst": {
        "Beginner": [
            ("Phishing triage", "A coworker reports a suspicious email. What safe first steps would you take?", "Checks safe triage and evidence handling.", "Do not click links or forward the message broadly.", "Preserve report; inspect headers safely; use reporting channel; escalate indicators.", "I would preserve the message through the approved reporting process, avoid opening links or attachments, collect headers and timestamps safely, and escalate using the organization's procedure."),
            ("Least privilege", "What does least privilege mean, and how would you apply it to a shared team account?", "Checks identity security basics.", "Start from the task that must be completed.", "Named accounts; minimum role; time-bound elevation; review and audit.", "I would avoid a shared account, assign named identities the minimum role needed, use time-bound elevation for exceptional work, and review access regularly."),
        ],
        "Intermediate": [
            ("Alert triage", "A SIEM raises repeated failed logins followed by a successful login. How would you triage this alert?", "Checks evidence-based incident triage.", "Correlate time, identity, source, and baseline without assuming compromise.", "Validate event sequence; correlate sources; assess risk; preserve evidence; escalate.", "I would confirm timestamps and identity, correlate source and device context, compare expected behavior, preserve relevant records, and escalate according to severity criteria without making unsupported claims."),
            ("Web assessment", "How would you safely assess an authorization issue in an application your team owns?", "Checks scope and non-destructive testing.", "Start with written authorization and test accounts.", "Written scope; test environment; controlled accounts; minimal evidence; remediation retest.", "I would confirm written scope, use dedicated test accounts in a non-production environment, verify only the agreed access boundary, capture minimal evidence, and report remediation and retest steps."),
        ],
        "Advanced": [
            ("Detection engineering", "How would you measure whether a new detection rule is useful before enabling high-severity alerts?", "Checks detection validation and false-positive management.", "Test against known positive and benign samples.", "Labeled test cases; precision/recall; coverage gaps; safe rollout; tuning ownership.", "I would test known positive and benign events, measure detection and false-positive behavior, document coverage gaps, run in a monitored mode, and assign tuning ownership before paging responders."),
            ("Incident leadership", "During a suspected incident, how would you balance containment, evidence preservation, and business continuity?", "Checks structured response under uncertainty.", "Follow the incident plan and record decision rationale.", "Severity and authority; containment options; evidence integrity; communications; recovery criteria.", "I would establish an incident lead, assess impact, choose proportionate containment under approved authority, preserve evidence, communicate through agreed channels, and define clear recovery and review criteria."),
        ],
    },
}

BEHAVIORAL_QUESTIONS = {
    "Beginner": ("Tell me about a time you had to learn a technical concept quickly.", "Understand learning habits and how you handle uncertainty.", "Situation and goal; learning plan; actions taken; result and reflection.", "In a class project I had to use a tool I had not seen before. I broke the task into small questions, used the documentation, built a tiny example, and asked for review. I finished the feature and learned to test assumptions early."),
    "Intermediate": ("Describe a time you found a problem late in a project. How did you respond?", "Understand ownership, communication, and prioritization.", "Situation and impact; your responsibility; actions and communication; result and prevention.", "Near a release I found an issue in a report. I checked its scope, told the team what was affected, proposed a safe correction, and verified the result before release. We added a check to catch it earlier next time."),
    "Advanced": ("Tell me about a difficult technical trade-off you influenced across a team.", "Understand judgment, collaboration, and accountability.", "Context and constraints; options; how you involved others; measurable outcome and learning.", "We had to choose between a fast patch and a broader change. I gathered failure and maintenance evidence, asked affected teammates about constraints, and documented the options. We chose a staged change with a rollback plan, reducing risk while keeping delivery on schedule."),
}


def interviews_for_career(career):
    result = {}
    prompts_by_level = TECHNICAL_QUESTIONS.get(career, {})
    if career == "Not Sure Yet":
        prompts_by_level = {
            "Beginner": [
                ("Career exploration", "How would you compare two technology roles when their job titles overlap?", "Checks structured exploration.", "Compare tasks and evidence, not just titles.", "Responsibilities; entry requirements; tools; work preferences; source quality.", "I would compare repeated responsibilities across several postings, identify the skills they require, and ask people in those roles about typical work before choosing a learning target."),
                ("Learning evidence", "How would you decide whether a new technical topic is worth studying further?", "Checks reflection and practical judgment.", "Try a small task and assess your interest and progress.", "Bounded experiment; learning resources; effort; interest; next step.", "I would choose a small, representative task, set a time limit, use reliable resources, and reflect on both the challenge and my interest before committing to a larger plan."),
            ],
            "Intermediate": [
                ("Portfolio direction", "How would you choose a portfolio project that helps you test a career direction?", "Checks project planning and evidence.", "Start from real role requirements and keep the scope testable.", "Role requirement; deliverable; evidence; feedback; reflection.", "I would select a repeated skill from relevant postings, define a small project that demonstrates it, get feedback from someone in the field, and use the result to refine my direction."),
                ("Skill gap", "How would you prioritize learning when a role lists many unfamiliar tools?", "Checks prioritization.", "Separate foundational requirements from optional tools.", "Frequency in postings; prerequisites; role level; fundamentals; practice.", "I would compare several role descriptions, prioritize shared foundational skills and prerequisites, and defer niche tools until a project or role requires them."),
            ],
            "Advanced": [
                ("Career decision", "What evidence would make you revise a career goal after investing time in it?", "Checks evidence-led decision making.", "Distinguish normal learning difficulty from a sustained mismatch.", "Interest over time; task fit; feedback; opportunities; alternative experiment.", "I would review my experience across real tasks, feedback, and opportunity data, then run a small comparison experiment before changing direction rather than reacting to one difficult week."),
                ("Transferable skills", "How would you explain transferable experience when applying to an entry-level technology role?", "Checks communication and role alignment.", "Connect a specific example to a responsibility in the target role.", "Role requirement; relevant example; action; outcome; learning gap.", "I would select a role requirement, describe a specific example with measurable outcome, explain how it transfers, and be clear about the technical areas I am still learning."),
            ],
        }
    for level, prompts in prompts_by_level.items():
        technical = []
        for index, item in enumerate(prompts, start=1):
            topic, question, evaluation, hint, key_points, sample = item
            technical.append({
                "key": f"{career}-{level}-technical-{index}".lower().replace(" ", "-"),
                "type": "technical",
                "level": level,
                "topic": topic,
                "question": question,
                "evaluation": evaluation,
                "hint": hint,
                "key_points": key_points,
                "sample_answer": sample,
            })
        question, intent, outline, sample = BEHAVIORAL_QUESTIONS[level]
        result[level] = technical + [{
            "key": f"{career}-{level}-behavioral-1".lower().replace(" ", "-"),
            "type": "behavioral",
            "level": level,
            "topic": "Behavioural · STAR",
            "question": question,
            "evaluation": intent,
            "hint": "Use the STAR structure: Situation, Task, Action, Result.",
            "key_points": outline,
            "sample_answer": sample,
        }]
    return result


DAY_TOPICS = {
    "Cloud Engineer": ["Linux navigation", "IP, DNS, and ports", "Cloud service models", "Object storage", "IAM roles", "Virtual machines", "Network boundaries", "Metrics and logs", "Container basics", "Deployment pipelines"],
    "Data Analyst": ["Spreadsheet quality checks", "SQL SELECT and WHERE", "Grouping and aggregation", "Joins and table grain", "Missing-value decisions", "Exploratory analysis", "Descriptive statistics", "Chart selection", "Dashboard measures", "Communicating caveats"],
    "Full Stack Developer": ["Semantic HTML", "Responsive CSS", "JavaScript state", "HTTP request and response", "Django routing", "Database relationships", "Form validation", "REST API design", "Authentication and ownership", "Testing and deployment"],
    "AI/ML Engineer": ["Python data types", "Data quality profiling", "Train/test separation", "Feature pipelines", "Regression metrics", "Classification thresholds", "Cross-validation", "Error analysis", "Model serving", "Drift monitoring"],
    "Android Developer": ["Kotlin types", "Functions and collections", "Compose or layout basics", "Activity lifecycle", "ViewModel state", "Room persistence", "Coroutines", "API error handling", "Background work", "Secure session storage"],
    "Cybersecurity Analyst": ["Account security", "Network fundamentals", "Linux permissions", "Safe email triage", "Log fields and timelines", "Alert severity", "Written scope and authorization", "Web security controls", "Detection testing", "Incident communication"],
}


JOB_ROLES = {
    "Cloud Engineer": [
        ("Cloud Support Associate", "Help users troubleshoot cloud services and document repeatable resolutions.", "Linux, Networking, Cloud fundamentals", "Triage support requests, reproduce issues, and escalate with clear evidence."),
        ("Junior Cloud Engineer", "Assist with provisioning and maintaining cloud environments.", "AWS or Azure, IAM, Linux", "Implement reviewed infrastructure changes and verify service health."),
        ("Cloud Operations Associate", "Monitor routine operations and support reliable service delivery.", "Monitoring, Linux, Incident basics", "Review alerts, follow runbooks, and maintain operational records."),
        ("DevOps Trainee", "Support automated build and deployment workflows.", "Git, CI/CD, Docker", "Maintain pipelines, investigate build failures, and improve deployment documentation."),
        ("Cloud Administrator", "Manage access, configuration, and inventory for cloud resources.", "IAM, Networking, Cost awareness", "Review access, apply approved configuration changes, and report resource usage."),
        ("Site Reliability Engineer", "Improve reliability through automation and service-level practices.", "Linux, Monitoring, Automation", "Measure reliability, reduce toil, and coordinate incident follow-up."),
    ],
    "Data Analyst": [
        ("Junior Data Analyst", "Turn operational data into clear, validated findings.", "SQL, Excel, Statistics", "Clean datasets, answer defined questions, and explain limitations."),
        ("MIS Executive", "Prepare recurring management information and operational reports.", "Excel, SQL, Data quality", "Maintain report schedules, reconcile totals, and flag anomalies."),
        ("Reporting Analyst", "Build and maintain reliable business reports.", "SQL, Power BI, Metric definitions", "Develop reports, validate measures, and coordinate definition changes."),
        ("Business Intelligence Analyst", "Model business data and make it accessible for decisions.", "SQL, Data modeling, Visualization", "Build semantic models and dashboards with documented measures."),
        ("Power BI Developer", "Create governed Power BI datasets and reports.", "Power BI, DAX, Data modeling", "Design measures, optimize reports, and manage refresh quality."),
        ("Product Analyst", "Analyze user and product behavior to inform product decisions.", "SQL, Experimentation, Statistics", "Define product metrics, investigate behavior, and communicate evidence."),
    ],
    "Full Stack Developer": [
        ("Junior Web Developer", "Build and maintain features across web interfaces and services.", "HTML, CSS, JavaScript", "Implement reviewed UI changes and fix browser-level issues."),
        ("Frontend Developer", "Create accessible user interfaces that work across devices.", "JavaScript, React, CSS", "Build components, integrate APIs, and validate usability."),
        ("Backend Developer", "Implement APIs, data models, and server-side workflows.", "Python or Node.js, SQL, APIs", "Build tested services and enforce validation and access control."),
        ("Full Stack Developer", "Deliver features across browser, application, and data layers.", "JavaScript, Django or Node.js, SQL", "Coordinate UI and API changes and maintain end-to-end tests."),
        ("Software Engineer", "Design, implement, and operate software as part of a product team.", "Programming, Testing, Git", "Deliver maintainable changes and participate in code review and support."),
    ],
    "AI/ML Engineer": [
        ("AI/ML Intern", "Support data preparation and baseline model experiments.", "Python, Pandas, Statistics", "Prepare reproducible datasets and record experiment results."),
        ("Junior Machine Learning Engineer", "Build and evaluate machine learning components.", "Python, scikit-learn, Model evaluation", "Develop pipelines, test models, and analyze errors."),
        ("Data Science Associate", "Explore datasets and communicate analytical or predictive findings.", "Python, SQL, Statistics", "Run analyses, validate assumptions, and present evidence."),
        ("AI Engineer", "Integrate AI capabilities into dependable applications.", "Python, APIs, Evaluation", "Build controlled integrations and assess output quality and risks."),
        ("MLOps Engineer", "Support reproducible training and model delivery systems.", "CI/CD, Containers, Monitoring", "Automate model packaging, deployment checks, and monitoring."),
    ],
    "Android Developer": [
        ("Android Developer Intern", "Help build and test Android application features.", "Kotlin, Android Studio, Git", "Implement scoped UI tasks and verify behavior on test devices."),
        ("Junior Android Developer", "Develop Android screens and connect them to application data.", "Kotlin, Activities or Compose, Testing", "Build lifecycle-aware features and fix reported defects."),
        ("Kotlin Developer", "Implement application logic and reusable Kotlin components.", "Kotlin, Coroutines, Unit testing", "Write maintainable code and verify edge cases."),
        ("Mobile Application Developer", "Build and maintain mobile experiences across app layers.", "Android, APIs, Persistence", "Integrate services, support offline states, and improve app reliability."),
    ],
    "Cybersecurity Analyst": [
        ("SOC Analyst L1", "Review security alerts and escalate activity using documented procedures.", "Logs, Networking, Triage", "Validate alerts, preserve relevant evidence, and document escalation."),
        ("Junior Security Analyst", "Support security monitoring, access reviews, and incident follow-up.", "Security fundamentals, IAM, Logs", "Investigate events and track remediation actions."),
        ("Vulnerability Assessment Analyst", "Assess authorized assets and report prioritized remediation.", "Networking, OWASP, Reporting", "Work within written scope and produce reproducible findings."),
        ("Penetration Testing Intern", "Assist with controlled security assessments in authorized environments.", "Web security, Scope control, Documentation", "Test only approved systems and communicate evidence and mitigations."),
        ("Security Operations Associate", "Coordinate operational security workflows and control checks.", "Incident process, Access control, Communication", "Maintain response records and support control improvements."),
        ("GRC Analyst", "Help maintain governance, risk, and compliance evidence.", "Risk analysis, Policies, Documentation", "Track control evidence, coordinate reviews, and report gaps."),
    ],
}


def job_roles_for_career(career):
    result = []
    roles = JOB_ROLES.get(career, [])
    if career == "Not Sure Yet":
        roles = [
            ("Technology Support Associate", "Help people resolve common software and device issues.", "Communication, troubleshooting, documentation", "Reproduce issues, document steps, and escalate clearly."),
            ("Junior Data Analyst", "Turn operational data into validated findings.", "SQL, Excel, Statistics", "Clean data, answer defined questions, and explain limitations."),
            ("Web Developer Intern", "Build and maintain small web features.", "HTML, CSS, JavaScript", "Implement scoped features and test browser behavior."),
        ]
    for title, description, skills, responsibilities in roles:
        entry_level = any(
            marker in title.casefold()
            for marker in ("junior", "intern", "trainee", "associate", "l1")
        )
        result.append({
            "title": title,
            "description": description,
            "skills": skills,
            "responsibilities": responsibilities,
            "role_kind": "Entry-level role" if entry_level else "Growth role",
        })
    return result
