# Design Brief for Hector Dog Blood Donor Web App

## Project Goal
Implement a frontend design for a web application connecting vet clinics with potential dog blood donors. The design should evoke **brightness, hope, friendliness, and professional hospital care**.

---

## Overall Aesthetic Principles

1. **Bright & Hopeful**: Ample white space and light background colors
2. **Friendly**: Soft, rounded elements, approachable typography, and welcoming messaging
3. **Professional Hospital Care**: Clean, organized, uncluttered layout with colors signifying cleanliness, trust, and calm

---

## I. General Styling Guidelines

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Primary Blue | `#A7D9EE` | Primary buttons, important highlights, interactive elements |
| Secondary Green | `#BEE6BE` | Success messages, secondary calls to action, supportive icons |
| Base White | `#FFFFFF` | Backgrounds and main content areas |
| Off-White | `#F8F8F8` | Subtle sectioning or background accents |
| Text Dark | `#333333` | Primary text for readability |
| Text Light | `#666666` | Secondary text, labels, less emphasized information |
| Text Placeholder | `#999999` | Placeholder text in inputs |
| Border Light | `#CCCCCC` | Input borders, subtle dividers |

### Typography

- **Font Family**: Clean, modern sans-serif (Inter, Roboto, Open Sans, or Lato)
- **Headings**: Use primary text color (#333333)
  - H1: Larger, bold for main screen titles
  - H2: Slightly smaller, semi-bold for section titles
  - H3: Smaller, regular or semi-bold for sub-sections
- **Body Text**: Regular weight, primary text color (#333333)
- **Labels/Small Text**: Lighter gray (#666666), slightly smaller font size

### Spacing & Layout

- **Ample White Space**: Generous padding and margins between elements
- **Grid-based Layout**: Responsive grid system for consistent alignment
- **Rounded Corners**: Subtle border-radius (4px - 8px for buttons/inputs, 8px - 12px for cards)

---

## II. Component-Specific Guidelines

### Buttons

#### Primary Buttons
- Background: Primary accent blue (#A7D9EE)
- Text: White (#FFFFFF)
- Border: None
- Hover/Active: Slightly darker shade of blue or subtle glow
- Border-radius: 4px-8px

#### Secondary Buttons
- Background: White (#FFFFFF)
- Text: Primary accent blue (#A7D9EE)
- Border: 1px solid primary accent blue (#A7D9EE)
- Hover/Active: Background fills with primary accent blue, text turns white
- Border-radius: 4px-8px

### Input Fields & Textareas

- Background: White (#FFFFFF)
- Border: Light gray (1px solid #CCCCCC)
- Focus State: Border changes to primary accent blue (#A7D9EE), subtle outline
- Placeholder Text: Light gray (#999999)
- Border-radius: 4px-8px

### Cards/Containers

- Background: White (#FFFFFF)
- Shadow: Subtle box-shadow for depth (e.g., `0px 2px 8px rgba(0,0,0,0.1)`)
- Border-radius: 8px-12px for a softer look

### Icons

- Library: Use consistent icon library (Font Awesome, Material Icons)
- Colors: Primary accent blue or secondary accent green for interactive/important icons, dark gray for informational icons
- Style: Outline or filled, but consistent throughout

---

## III. Screen-Specific Instructions

### Donor Dashboard
- **Layout**: Clear sections for "My Profile," "My Dogs," "Donation History," and "Active Requests"
- Use cards for displaying requests and dog profiles
- Prominent "Register New Dog" or "Find Opportunities" Call to Action

### Clinic Dashboard
- **Layout**: Sections for "My Clinic Profile," "My Blood Requests," and "Available Donors"
- Easy access to "Post New Request" button
- Donor list should be clean and filterable

### Donor Registration
- Multi-step form with clear progress indicators at the top (dots or numbered steps)
- Each step should have a clear title and instructions
- Input fields should be well-spaced and easy to complete

### Blood Request Form
- Clean, single-page form with logical grouping of fields
  - "Request Details"
  - "Patient Information"
  - "Contact Info"
- Clear labels and helpful placeholder text
- "Submit Request" button should be a primary button

---

## Implementation Status

### ✅ Completed
- Color system configured in TailwindCSS
- Typography system with Inter font family
- Button components (primary and secondary)
- Input field styling
- Card component styling
- Base layout structure

### 🚧 In Progress
- Page-specific components
- Form components
- Icon system integration

### 📋 To Do
- Multi-step form component
- Data table/list components
- Modal/dialog components
- Toast notification system
