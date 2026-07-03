1. **Directory Structure & Routing Skeletons**: Establish the Next.js page routing structure (`/`, `/lite-version`, `/technical-version`, `/delphi-proposal`, `/login`, `/register`, `/upload`, `/dashboard`, `/validate`, `/admin`) using empty placeholder components to register all routes.
2. **Global Styling & Typography Foundation**: Configure CSS variables and layout components (Navbar, Footer) matching MIDAS's design system: serif headers (Georgia/Iowan Old Style), sans-serif body text (Aptos/Segoe UI), color palette (navy/blue primary, orange accent, warm white background), and custom scrollbars/borders.
3. **Static UI: Landing & Document Pages**: Build pixel-perfect static mockups for the homepage (all sections including hero, stats, cards, CTA) and the public reference pages (Lite, Technical, and Delphi Proposal specifications).
4. **Static UI: Interactive & Auth Pages**: Construct static layouts for Login/Register, the multi-step Metadata Intake/Upload Wizard, and the User/Admin Dashboards.
5. **Auth & State Integration**: Wire up the Login/Register forms to the backend FastAPI JWT authentication endpoint, configuring secure HttpOnly cookies, route guards, and auth context states.
6. **Core Upload & Scoring Integration**: Connect the upload wizard to the async FastAPI processing engine (Celery/Redis), showing dynamic loading states, processing statuses, and final CQI/PRS scores.
7. **Dashboard & Delphi Integration**: Connect the User/Admin dashboards and Delphi validation panels to backend endpoints to display actual assessment history, scores, and consensus feedback.
8. **Polish, Responsive Adjustments, & Animations**: Adjust layouts for fluid responsive breakpoints (mobile/desktop) and implement smooth CSS/framer-motion transitions and scroll-reveals.
9. **Security Hardening**: Verify secure cookie attributes, add form validation, sanitize user inputs, and check security headers matching the threat model checklist.
10. **Cleanup & Unused Code Pruning**: Safely locate and delete any redundant placeholder stubs, draft styling, or unused components/assets from the template.

### Rule: API & Integration Discrepency Logging

During any frontend task or checkpoint execution, if you identify a discrepancy between the frontend expectations and backend requirements (e.g., mismatched data structures, missing API endpoints, incompatible parameter names, type mismatches, or broken route parameters), you **MUST** pause implementation and log the discrepancy immediately.

All discrepancies must be recorded in [discrepency.md](file:///Users/prabhavtrivedi/Desktop/AI-KOSH-TOOLKIT/discrepency.md) in the following table format:

| ID | Component/Route | Mismatched Files & Line Numbers | Description of Discrepancy | Backend Expectation | Frontend Implementation / Draft | Proposed Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `D-001` | e.g. `/api/v1/auth` | [auth.py:L40](file:///path/to/backend/auth.py#L40) <br> [login.tsx:L12](file:///path/to/frontend/login.tsx#L12) | Mismatch on login payload field name for user identification. | Expects `username` | Sending `email` | Update frontend login component payload to use `username`. |

**Instructions for Agents:**
1. Document the discrepancy before attempting to write a fix.
2. Provide exact file links using absolute workspace paths with line references (`file:///...#L12-L15`).
3. Increment the ID sequence (`D-001`, `D-002`, etc.) for each distinct issue.
4. If a resolution requires significant changes to the OpenAPI contract, seek user confirmation before proceeding.