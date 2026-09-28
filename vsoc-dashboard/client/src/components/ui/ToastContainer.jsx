import React from 'react';
import Toast from './Toast';
import { useToast } from '../../context/ToastContext';

const ToastContainer = () => {
  const { toasts, removeToast } = useToast();

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map(toast => (
        <Toast key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>
  );
};

export default ToastContainer;
