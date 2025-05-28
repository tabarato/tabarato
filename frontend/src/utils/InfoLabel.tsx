import { motion } from "framer-motion";

type InfoLabelProps = {
  text: string;
  color?: "primary" | "secondary" | "accent" | "success" | "warning" | "error";
};

const InfoLabel = ({ text, color = "primary" }: InfoLabelProps) => {
  return (
    <motion.div
        initial={{ x: -150, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 150, damping: 18 }}
        whileHover={{ scale: 1.05 }}
      className={`whitespace-nowrap rounded-lg mb-6 border-${color} bg-${color} bg-opacity-90 pl-2 py-2 text-sm font-semibold text-base-100 shadow-lg`}
    >
      <motion.div
        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
      >
        {text}
      </motion.div>
    </motion.div>
  );
};

export default InfoLabel;
