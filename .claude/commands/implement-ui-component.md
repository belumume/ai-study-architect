# Implement UI Component

Create a new React component following our design system and best practices.

## Steps:

1. First look at existing components in `frontend/src/components/` to understand:
   - Component structure and organization
   - Material-UI usage patterns
   - TypeScript interfaces and props
   - How components communicate

2. If a mockup or screenshot is provided, analyze it carefully for:
   - Layout requirements
   - Interactive elements
   - Responsive design needs
   - Accessibility considerations

3. Write component tests FIRST in `frontend/src/components/__tests__/`:
   - Test rendering with different props
   - Test user interactions
   - Test edge cases and error states
   - Test accessibility (aria labels, keyboard navigation)

4. Implement the component:
   - Use functional components with hooks
   - Define TypeScript interfaces for props
   - Use Material-UI components and theme
   - Implement responsive design
   - Add proper aria labels for accessibility

5. Take a screenshot of the implemented component and compare with mockup (if provided)

6. Iterate on the implementation 2-3 times for best visual results

7. Run tests and type checking:
   ```bash
   npm test -- YourComponent.test.tsx
   npm run typecheck
   ```

8. Ensure linting passes:
   ```bash
   npm run lint
   ```

Component description and requirements: $ARGUMENTS