/**
 * Archangel Health Logo Component
 * Figma-designed logo for the landing page.
 */

import { motion } from "motion/react";

export default function ArchangelHealthLogo() {
  return (
    <>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.2 }}
        className="fixed top-6 left-6 md:top-8 md:left-8 z-[100]"
      >
        <span className="archangel-logo-text">ARCHANGEL HEALTH</span>
      </motion.div>

      <style>{`
        .archangel-logo-text {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          font-weight: 600;
          font-size: 0.9375rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: #f5f5f7;
          opacity: 0.85;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }

        @media (min-width: 768px) {
          .archangel-logo-text {
            font-size: 1.0625rem;
          }
        }
      `}</style>
    </>
  );
}
