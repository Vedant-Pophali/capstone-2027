import React, { useState } from 'react';
import Modal from '../ui/Modal';
import { useToast } from '../../context/ToastContext';
import { apiService } from '../../services/api';

const AddVehicleModal = ({ isOpen, onClose, onSuccess, existingVehicles = [] }) => {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ id: '', owner: '', model: '' });

  // Client-side duplicate check for instant feedback
  const isDuplicate = form.id.trim() !== '' &&
    existingVehicles.some(v => v.id === form.id.trim());

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.id.trim() || isDuplicate) return;

    setLoading(true);
    try {
      await apiService.createVehicle({
        id: form.id.trim(),
        owner: form.owner.trim(),
        model: form.model.trim(),
      });
      addToast(`Vehicle #${form.id} created and container started`, 'success');
      setForm({ id: '', owner: '', model: '' });
      onSuccess?.();
      onClose();
    } catch (err) {
      addToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const footer = (
    <>
      <button className="btn btn-secondary" onClick={onClose} disabled={loading}>
        Cancel
      </button>
      <button className="btn btn-primary" onClick={handleSubmit} disabled={loading || !form.id.trim() || isDuplicate}>
        {loading ? 'Creating...' : 'Create Vehicle'}
      </button>
    </>
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add New Vehicle" footer={footer}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="vehicle-id">Vehicle ID *</label>
          <input
            id="vehicle-id"
            className={`form-input${isDuplicate ? ' input-error' : ''}`}
            name="id"
            value={form.id}
            onChange={handleChange}
            placeholder="e.g. 42"
            pattern="^[a-zA-Z0-9_-]+$"
            required
            autoFocus
          />
          {isDuplicate ? (
            <div className="form-hint" style={{ color: 'var(--color-error, #f87171)' }}>
              ⚠ Vehicle ID already exists in the fleet.
            </div>
          ) : (
            <div className="form-hint">Alphanumeric characters, hyphens, and underscores only.</div>
          )}
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
          />
        </div>
      </form>
    </Modal>
  );
};

export default AddVehicleModal;
