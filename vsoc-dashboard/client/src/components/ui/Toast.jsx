import React from 'react';
import { CheckCircle, XCircle, Info, X } from 'lucide-react';

const icons = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
};

const Toast = ({ toast, onClose }) => {
  const Icon = icons[toast.type] || Info;

  return (
    <div className={`toast ${toast.type}`} role="alert">
      <Icon className="toast-icon" />
      <span className="toast-message">{toast.message}</span>
      <button className="toast-close" onClick={() => onClose(toast.id)} aria-label="Dismiss">
        <X size={14} />
      </button>
    </div>
  );
};

export default Toast;
