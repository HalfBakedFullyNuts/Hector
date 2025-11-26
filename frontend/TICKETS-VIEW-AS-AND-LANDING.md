# Feature Tickets: View As & Landing Page

## Overview
This document outlines tickets for implementing:
1. Admin "View As" role switching feature
2. Public landing page with hero section
3. Master admin credentials reference

---

## T-1000: Create Master Admin Credentials Reference

**Priority:** High
**Estimate:** Small

### Description
Create a reference file documenting the master admin account credentials for development/testing.

### Acceptance Criteria
- [ ] Create `ADMIN_CREDENTIALS.md` in project root
- [ ] Document master admin username: `admin`
- [ ] Document master admin password: `admin`
- [ ] Add security warning about changing credentials in production

### Files to Create
- `/ADMIN_CREDENTIALS.md`

---

## T-1001: Implement "View As" Context and State Management

**Priority:** High
**Estimate:** Medium

### Description
Create a context to manage the "View As" functionality, allowing admins to impersonate other roles without logging into different accounts.

### Acceptance Criteria
- [ ] Create `ViewAsContext.tsx` with state for viewing role
- [ ] Store original admin user separately from "viewed as" role
- [ ] Provide functions: `setViewAs(role)`, `clearViewAs()`, `isViewingAs`
- [ ] Persist "view as" state in sessionStorage (clears on browser close)
- [ ] Only ADMIN role can use "View As"

### Technical Details
```typescript
interface ViewAsContextType {
  viewingAs: UserRole | null;  // The role being impersonated
  setViewAs: (role: UserRole) => void;
  clearViewAs: () => void;
  isViewingAs: boolean;
  effectiveRole: UserRole;     // Returns viewingAs or actual user role
}
```

### Files to Create
- `/src/contexts/ViewAsContext.tsx`

### Files to Modify
- `/src/App.tsx` - Wrap with ViewAsProvider

---

## T-1002: Create View As Selector Component

**Priority:** High
**Estimate:** Medium

### Description
Create a UI component for admins to select which role to view the app as.

### Acceptance Criteria
- [ ] Dropdown/select to choose role (DOG_OWNER, CLINIC_STAFF, ADMIN)
- [ ] Visual indicator showing current "View As" status
- [ ] "Exit View As" button to return to admin view
- [ ] Banner/badge showing "Viewing as [ROLE]" when active
- [ ] Only visible to users with ADMIN role

### UI Design
- Position: Top bar or floating component
- Colors: Warning/orange tint when viewing as another role
- Clear "Exit" button to return to normal admin view

### Files to Create
- `/src/components/admin/ViewAsSelector.tsx`
- `/src/components/admin/ViewAsBanner.tsx`

---

## T-1003: Integrate View As with Protected Routes

**Priority:** High
**Estimate:** Medium

### Description
Modify the ProtectedRoute component to use the effective role from ViewAsContext instead of the actual user role.

### Acceptance Criteria
- [ ] ProtectedRoute checks `effectiveRole` from ViewAsContext
- [ ] Admin viewing as DOG_OWNER can access /owner routes
- [ ] Admin viewing as CLINIC_STAFF can access /clinic routes
- [ ] Navigation menu updates based on effective role
- [ ] Dashboard redirects work with effective role

### Files to Modify
- `/src/components/common/ProtectedRoute.tsx`
- `/src/components/layout/DashboardLayout.tsx`

---

## T-1004: Integrate View As with Dashboard Layout

**Priority:** Medium
**Estimate:** Small

### Description
Update the DashboardLayout to show the ViewAsBanner and adapt navigation based on effective role.

### Acceptance Criteria
- [ ] Show ViewAsBanner at top when viewing as another role
- [ ] Sidebar navigation reflects effective role
- [ ] User info section shows "Viewing as [ROLE]" indicator
- [ ] ViewAsSelector available in admin navigation

### Files to Modify
- `/src/components/layout/DashboardLayout.tsx`

---

## T-1005: Create Public Landing Page

**Priority:** High
**Estimate:** Large

### Description
Create a public landing page with hero section, app information, and login button.

### Acceptance Criteria
- [ ] Hero section with:
  - [ ] Headline about dog blood donation
  - [ ] Subheadline with value proposition
  - [ ] CTA button to login/register
  - [ ] Placeholder image area (200x200 or similar)
- [ ] Features section with 3-4 feature cards
- [ ] How it works section (3 steps)
- [ ] Call to action section
- [ ] Footer with basic links
- [ ] Responsive design (mobile-first)
- [ ] Use Lorem Ipsum for all text content

### UI Sections
1. **Hero**: Full-width, centered content, placeholder image
2. **Features**: Grid of 3-4 cards with icons (use placeholder icons)
3. **How It Works**: 3-step process with numbers
4. **CTA**: Final call to action with register button
5. **Footer**: Copyright, links

### Files to Create
- `/src/pages/public/LandingPage.tsx`
- `/src/components/landing/HeroSection.tsx`
- `/src/components/landing/FeaturesSection.tsx`
- `/src/components/landing/HowItWorksSection.tsx`
- `/src/components/landing/CTASection.tsx`
- `/src/components/landing/Footer.tsx`

---

## T-1006: Create Public Layout Component

**Priority:** Medium
**Estimate:** Small

### Description
Create a layout component for public pages (landing, login, register) with consistent header/footer.

### Acceptance Criteria
- [ ] Simple header with logo/app name and Login button
- [ ] Footer component
- [ ] No sidebar (unlike dashboard layout)
- [ ] Clean, marketing-focused design

### Files to Create
- `/src/components/layout/PublicLayout.tsx`

---

## T-1007: Update Routing for Landing Page

**Priority:** High
**Estimate:** Small

### Description
Update the app routing to show landing page at root and move login to /login.

### Acceptance Criteria
- [ ] `/` shows LandingPage (public)
- [ ] `/login` shows LoginPage
- [ ] `/register` shows RegisterPage
- [ ] Authenticated users redirected from landing to their dashboard
- [ ] Remove auto-redirect from `/` to `/login`

### Files to Modify
- `/src/App.tsx`

---

## T-1008: Update Login Page Integration

**Priority:** Medium
**Estimate:** Small

### Description
Update the login page to work with the new landing page flow.

### Acceptance Criteria
- [ ] "Back to home" link on login page
- [ ] After login, redirect to appropriate dashboard based on role
- [ ] Master admin (admin/admin) can log in successfully in DEV_MODE

### Files to Modify
- `/src/pages/auth/LoginPage.tsx`
- `/src/contexts/AuthContext.tsx` - Add master admin to mock users

---

## Implementation Order

1. **T-1000**: Create credentials reference (quick setup)
2. **T-1005**: Create Landing Page components
3. **T-1006**: Create Public Layout
4. **T-1007**: Update routing for landing page
5. **T-1008**: Update login integration
6. **T-1001**: Implement View As Context
7. **T-1002**: Create View As Selector component
8. **T-1003**: Integrate with Protected Routes
9. **T-1004**: Integrate with Dashboard Layout

---

## Notes

- All text content uses Lorem Ipsum placeholders
- All images use placeholder boxes with descriptive text
- Master admin credentials are for DEV_MODE only
- View As feature only available to ADMIN role users
- Session storage used for View As to prevent persistence across sessions
