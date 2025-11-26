/**
 * CTA (Call to Action) Section Component
 * Final call to action before footer
 */

import { Link } from 'react-router-dom';

export const CTASection: React.FC = () => {
  return (
    <section className="py-20 px-4 bg-primary-blue">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-text-dark mb-4">
          Ready to Make a Difference?
        </h2>
        <p className="text-lg text-text-dark/80 mb-8 max-w-2xl mx-auto">
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
          tempor incididunt ut labore et dolore magna aliqua. Join thousands of dog
          owners who are helping save lives.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/register"
            className="px-8 py-4 bg-text-dark hover:bg-text-dark/90 text-white font-semibold rounded-button text-lg transition-colors"
          >
            Get Started Today
          </Link>
          <Link
            to="/login"
            className="px-8 py-4 bg-white/90 hover:bg-white text-text-dark font-semibold rounded-button text-lg transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>
    </section>
  );
};
