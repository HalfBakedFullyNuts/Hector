/**
 * Hero Section Component
 * Main banner section for the landing page
 */

import { Link } from 'react-router-dom';
import heroImage from '../../assets/hero-dog.jpg';

export const HeroSection: React.FC = () => {
  return (
    <section className="bg-gradient-to-br from-primary-blue/20 to-secondary-green/20 py-20 px-4">
      <div className="max-w-6xl mx-auto flex flex-col lg:flex-row items-center gap-12">
        {/* Text Content */}
        <div className="flex-1 text-center lg:text-left">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-dark mb-6">
            Save a Dog's Life Today
          </h1>
          <p className="text-xl md:text-2xl text-text-light mb-8 max-w-2xl">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
            tempor incididunt ut labore et dolore magna aliqua. Connect your healthy
            dog with those in need of blood donations.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
            <Link
              to="/register"
              className="px-8 py-4 bg-primary-blue hover:bg-primary-blue-dark text-text-dark font-semibold rounded-button text-lg transition-colors"
            >
              Register Your Dog
            </Link>
            <Link
              to="/login"
              className="px-8 py-4 bg-white hover:bg-gray-50 text-text-dark font-semibold rounded-button text-lg border border-border transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Hero Image */}
        <div className="flex-1 flex justify-center">
          <div className="w-80 h-80 md:w-96 md:h-[28rem] overflow-hidden rounded-card shadow-xl">
            <img
              src={heroImage}
              alt="A beautiful black Labrador resting on a log in nature"
              className="w-full h-full object-cover object-center"
            />
          </div>
        </div>
      </div>
    </section>
  );
};
