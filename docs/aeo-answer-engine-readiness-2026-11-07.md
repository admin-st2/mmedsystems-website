# MMeD Systems — AEO / Generative AI Search Readiness

**Status:** Content plan and audit only. NOT a website deployment or approved copy revision.  
**Prepared:** November 7, 2026  
**Current public website:** https://mmedsystems.com/ (custom GitHub Pages site)  
**Review branch:** `staging` (staging Pages site itself is not yet activated behind Cloudflare Access).

## Goal

Make MMeD Systems easier for healthcare decision makers to find, understand and evaluate when they ask search engines and AI assistants questions about EMR/EHR and healthcare management technology. AEO (Answer Engine Optimization), GEO and conventional SEO overlap. **The priority is original, accurate, easily indexed information**, not special AI markup.

## Source-verified baseline (current repository, November 7)

- `robots.txt` reads `User-agent: *\nAllow: /\nSitemap: https://mmedsystems.com/sitemap.xml`. This does not deliberately block OAI-SearchBot or Bingbot. An on-site robots check **does not** guarantee that CDN/hosting/WAF requests are actually served; verify external crawl behavior separately.
- `index.html` includes Organization, WebSite and WebPage JSON-LD, but the homepage does not currently answer common buyer questions in explicit question-and-answer form.
- Most solution pages contain generic descriptions and workflow lists, with no clearly labeled FAQ section. `where-we-serve/` already contains several questions and answers; verify statements that imply service or availability in particular countries.
- `security/` discusses intentions and design principles, not certified compliance; it should remain explicit about what has and has not been independently verified.
- `request-demo/` uses a mailto contact path. The secure lead backend PR #11 remains draft and disabled. Never claim that the website form sends a confirmed request until it is actually operational.
- Actual AI referral/citation analytics are **not verified**. Prior GSC Wizard trial was reported expired. No new paid service is needed to draft helpful copy, but first-party Google Search Console and Bing Webmaster access will be required for objective performance reports.
- Current live marketing copy must not assert production deployments, clinic testimonials, integration partnerships, guaranteed pricing/features, medical certifications, security compliance or client results unless supported by reviewed evidence.

## Content design without visual redesign

Keep the existing white/navy palette, Times New Roman, URLs, H1s and section layouts. AEO is a **content and technical-accuracy layer**, not another website redesign. Proposed changes must be separately reviewed and implemented on private staging before any public merge.

### Highest priority — buyer questions

| Page | Reader question to address clearly | Evidence and scope guardrails |
| --- | --- | --- |
| Home | What does MMeD Systems do, and which organizations is it designed for? | 2–3 direct sentences, link to Solutions and Request a Demo; distinguish design/roadmap from live product capabilities. |
| `/private-clinics/` | What should a small practice evaluate when selecting an EMR/EHR? | Focus on appointments, charting, medications, referrals, billing handoffs, privacy and rollout. Do **not** call unverified features generally available. |
| `/medical-centers/` | How can multiple medical departments coordinate records, lab results, pharmacy and finance? | Explain workflows and responsibilities with a simple realistic (fictional) journey. |
| `/hospitals/` | What must hospital information systems handle at departmental and enterprise scale? | Discuss design priorities and limitations, including testing, audits, ERP/SCM and local requirements; do not claim proven hospital-scale deployments. |
| `/integrations/` | What is HL7/FHIR interoperability, and how are healthcare systems integrated? | Explain standards in original language with links to relevant authoritative standards and verify MMeD-specific support before advertising it. |
| `/security/` | How does MMeD approach access controls, audit trails, data location and HIPAA responsibilities? | Clearly distinguish plans, implemented technical controls, BAA readiness and certified evidence. There is no official HIPAA product certification to invent. |
| `/request-demo/` | How do I request an MMeD demonstration, and what happens next? | Current inquiry is email-based; NDA and invite rules are separate. Never ask for patient information via public inquiry. |
| `/where-we-serve/` | Which markets is MMeD engaging and how are local workflows evaluated? | Distinguish target markets and discussions from supported deployments, physical offices and regulatory approval. |
| `/resources/` | What should I ask before selecting or migrating to EMR/EHR software? | Publish a useful, original and reviewable checklist, not copied vendor claims. |
| `/pricing/` (pending) | What are the pricing tiers, what is included and which terms remain uncertain? | Pricing figures have been supplied, but exact final feature lists, fees, terms and discounts still await approval. Do not publish unapproved terms. |

### Proposed question/answer drafting pattern

**Question:** How should a clinic evaluate a new EMR?  
**Answer outline:** Start with scheduling and registration, clinical documentation, medication and order workflows, referrals, billing handoffs, staff permissions, reporting, data migration, training, and continuity of care. Then compare those needs against what each vendor can actually demonstrate.

**Question:** Is a private MMeD clinical demo the same as a production deployment?  
**Answer outline:** No. Demonstrations use fictional records under invitation and NDA rules. Production deployment requires a separate scope and security/compliance assessment.

**Question:** Can MMeD work with healthcare organizations outside the United States?  
**Answer outline:** MMeD welcomes conversations in U.S., African and other international markets. Country-specific regulatory, language, hosting, payment and integration requirements are assessed individually; marketing interest is not proof of a live local deployment.

**Question:** Does MMeD certify that any hospital installation is HIPAA-compliant?  
**Answer outline:** Do not make blanket certification claims. U.S. regulated deployments need an appropriate risk assessment, agreements, technical controls and operating procedures for the specific environment.

The precise website copy is **not approved**. These are structured editorial prompts to refine with the owner and, for healthcare regulations, appropriate reviewers.

## Technical and AI search eligibility

1. Maintain indexable public HTML, one primary H1, self-canonical URLs, meaningful headings, readable DOM text and internal links. Keep private demo, staging and prototypes blocked from indexing.
2. Do not automatically add `FAQPage` structured data to every page. Visible user questions are worthwhile, but Google's FAQ rich-result eligibility is restricted, and schema must match the actual visible content. Review supported types separately.
3. Retain truthful `Organization`, `WebSite` and relevant `WebPage` JSON-LD; add factual `BreadcrumbList` only where breadcrumb content is actually visible and the markup is accurate. Validate all changes.
4. OpenAI's `OAI-SearchBot` is a *search-discovery* crawler and separately controllable from `GPTBot`, used for model training. Current general `Allow: /` does not disallow either, but first-party crawling logs/WAF checks are still needed. A company can choose to allow SearchBot without opting into training. Make this an owner policy decision if explicit changes are proposed.
5. Google explicitly says Google Search/AI Mode does not require an `llms.txt` file or special AEO markup. Do **not** ship such a file on speculative ranking promises.
6. Optimize authentic figures, explanatory screenshots and video: informative alt text, captions/transcripts, descriptive filenames and fictional-only patient data. No fabricated product UI screenshots.
7. Prefer original source-backed articles and clear product status over country doorway pages, keyword stuffing, manufactured citations, fake clients or unverified integrations.

## How to measure progress (free-first)

- **Google Search Console:** public page indexing, crawl status, impressions/clicks by page, search terms and countries; use any available first-party AI feature report rather than invent AI visibility totals.
- **Bing Webmaster Tools:** indexation plus **AI Performance** citations, cited URLs and grounding query groups across supported AI surfaces (these are citations, not clicks; coverage is sampled and non-exhaustive).
- **Website analytics:** with permissioned, privacy-conscious instrumentation, analyze qualified demo inquiries, contact sales engagement, and AI referral sessions without capturing PHI.
- **Manual spot checks:** retain a fixed list of buyer prompts and record whether major AI/search engines cite or describe MMeD accurately; do not treat one-off responses as ranking proof.
- Review results monthly and focus on qualified conversations, not just raw search visibility.

## Implementation order / owner gate

1. Finish owner review of buttons/navigation and responsive spacing (draft PRs #20, #21); do not push unrelated AEO design changes into them.
2. Establish the Access-protected clickable private staging website and verify anonymous visitors are denied.
3. Draft a **small, owner-approved Q&A content improvement set** for `/private-clinics/`, `/medical-centers/`, `/integrations/`, `/security/` and `/request-demo/`, using the **existing layout and content meaning**.
4. Verify any provider or hospital claim with real engineering evidence, product screenshots, compliance documentation and customer permissions before publishing.
5. Validate link destinations, accessibility, structured data and mobile UX in staging; then request explicit approval before a production merge.
6. Recheck Google Search Console/Bing crawlability and AI citation data after release. No paid SEO/AEO tool is required to start.

## Primary public references (checked November 7, 2026)

- Google Search Central: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Google AI features: https://developers.google.com/search/docs/appearance/ai-features
- Bing Webmaster Guidelines: https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a
- Bing AI Performance: https://www.bing.com/webmasters/help/ai-performance-9f8e7d6c
- OpenAI crawlers: https://developers.openai.com/api/docs/bots
