/**
 * How It Works Section Component
 * Shows the 3-step process for using the platform
 */

const steps = [
  {
    number: '1',
    title: 'Register Your Dog',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Create a profile for your furry friend with health information and blood type.',
  },
  {
    number: '2',
    title: 'Get Matched',
    description:
      'Ut enim ad minim veniam, quis nostrud exercitation. Our system matches your dog with recipients who need compatible blood donations.',
  },
  {
    number: '3',
    title: 'Visit a Clinic',
    description:
      'Duis aute irure dolor in reprehenderit in voluptate. Schedule an appointment at a partner veterinary clinic to complete the donation.',
  },
];

export const HowItWorksSection: React.FC = () => {
  return (
    <section className="py-20 px-4 bg-base-off-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-text-dark mb-4">
            How It Works
          </h2>
          <p className="text-lg text-text-light max-w-2xl mx-auto">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Getting started
            is simple and only takes a few minutes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step, index) => (
            <div key={index} className="relative">
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-12 left-1/2 w-full h-0.5 bg-primary-blue/30" />
              )}

              <div className="bg-white p-8 rounded-card text-center relative z-10">
                {/* Step number */}
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-blue text-text-dark text-2xl font-bold rounded-full mb-6">
                  {step.number}
                </div>

                <h3 className="text-xl font-semibold text-text-dark mb-3">
                  {step.title}
                </h3>
                <p className="text-text-light">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
