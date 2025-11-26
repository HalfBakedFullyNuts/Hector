/**
 * Landing Page
 * Public home page for the Hector dog blood donation platform
 */

import { HeroSection } from '../../components/landing/HeroSection';
import { FeaturesSection } from '../../components/landing/FeaturesSection';
import { HowItWorksSection } from '../../components/landing/HowItWorksSection';
import { CTASection } from '../../components/landing/CTASection';
import { Footer } from '../../components/landing/Footer';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1">
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
};
