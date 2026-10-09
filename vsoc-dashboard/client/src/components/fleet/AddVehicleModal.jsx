import React, { useState } from 'react';
import Modal from '../ui/Modal';
import { useToast } from '../../context/ToastContext';
import { apiService } from '../../services/api';

const AddVehicleModal = ({ isOpen, onClose, onSuccess }) => {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [form, setForm] = useState({ id: '', owner: '', model: '' });

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
    if (submitError) setSubmitError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.id.trim()) return;

    setLoading(true);
    setSubmitError('');
    try {
      await apiService.createVehicle({
        id: form.id.trim(),
        owner: form.owner.trim(),
        model: form.model.trim(),
      });
      addToast(`Vehicle #${form.id} registered — container started`, 'success');
      setForm({ id: '', owner: '', model: '' });
      onSuccess?.();
      onClose();
    } catch (err) {
      setSubmitError(err.message || 'Failed to create vehicle. Is the edge-vehicle image built?');
    } finally {
      setLoading(false);
    }
  };

  const footer = (
    <>
      <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
        Cancel
      </button>
      <button className="btn btn-primary" onClick={handleSubmit} disabled={loading || !form.id.trim()}>
        {loading ? 'Creating...' : 'Create Vehicle'}
      </button>
    </>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Deploy Edge Vehicle" footer={footer}>
      <form onSubmit={handleSubmit}>
        {submitError && (
          <div className="form-error-banner" role="alert">
            <strong>Container error:</strong> {submitError}
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="vehicle-id">Vehicle ID *</label>
          <input
            id="vehicle-id"
            className="form-input"
            name="id"
            value={form.id}
            onChange={handleChange}
            placeholder="e.g. 42"
            pattern="^[a-zA-Z0-9_\-]+$"
            required
            autoFocus
            disabled={loading}
          />
          <div className="form-hint">Alphanumeric, hyphens, and underscores only. Becomes the container name.</div>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="vehicle-owner">Owner</label>
          <input
            id="vehicle-owner"
            className="form-input"
            name="owner"
            value={form.owner}
            onChange={handleChange}
            placeholder="e.g. Vedant"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="vehicle-model">Vehicle Model</label>
          <input
            id="vehicle-model"
            className="form-input"
            name="model"
            value={form.model}
            onChange={handleChange}
            placeholder="e.g. Tesla Model 3"
            disabled={loading}
          />
        </div>
      </form>
    </Modal>
  );
};

export default AddVehicleModal;
