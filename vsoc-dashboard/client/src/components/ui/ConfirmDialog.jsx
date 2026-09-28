import React from 'react';
import { AlertTriangle } from 'lucide-react';
import Modal from './Modal';

const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, message, confirmLabel = 'Delete', loading = false }) => {
  const footer = (
    <>
      <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
        Cancel
      </button>
      <button
        className="btn btn-confirm-danger"
        onClick={onConfirm}
        disabled={loading}
      >
        {loading ? 'Processing...' : confirmLabel}
      </button>
    </>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title || 'Confirm Action'} footer={footer}>
      <div className="confirm-body">
        <div className="confirm-icon">
          <AlertTriangle size={24} />
        </div>
        <p>{message || 'Are you sure? This action cannot be undone.'}</p>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;
