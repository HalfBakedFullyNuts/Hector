/**
 * Button Component
 * Reusable button with variants
 */

import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
  children: React.ReactNode;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  children,
  fullWidth = false,
  className = '',
  ...props
}) => {
  const baseClass = variant === 'primary' ? 'btn-primary' : 'btn-secondary';
  const widthClass = fullWidth ? 'w-full' : '';
  const combinedClass = `${baseClass} ${widthClass} ${className}`.trim();

  return (
    <button className={combinedClass} {...props}>
      {children}
    </button>
  );
};

export default Button;
