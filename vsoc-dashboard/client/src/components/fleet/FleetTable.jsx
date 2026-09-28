import React, { useState } from 'react';
import { Plus, Car, Trash2, RefreshCw } from 'lucide-react';
import StatusBadge from '../ui/StatusBadge';
import ConfirmDialog from '../ui/ConfirmDialog';
import Spinner from '../ui/Spinner';
import { useToast } from '../../context/ToastContext';
import { apiService } from '../../services/api';

const FleetTable = ({ vehicles, loading, onRefresh, onOpenAddModal }) => {
  const { addToast } = useToast();
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await apiService.deleteVehicle(deleteTarget);
      addToast(`Vehicle #${deleteTarget} removed and container destroyed`, 'success');
      onRefresh?.();
    } catch (err) {
      addToast(err.message, 'error');
    } finally {
      setDeleting(false);
      setDeleteTarget(null);
    }
  };

  const formatContainerId = (id) => {
    if (!id) return '—';
    return id.substring(0, 12);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString([], {
        month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch {
      return '—';
    }
  };

  const containerBadgeClass = (status) => {
    if (!status) return 'pending';
    return status.toLowerCase();
  };

  return (
    <>
      <div className="table-container">
        <div className="table-header">
          <h2>Fleet Vehicles</h2>
          <div className="table-header-actions">
            <button className="btn btn-secondary" onClick={onRefresh} title="Refresh">
              <RefreshCw size={16} />
              <span>Refresh</span>
            </button>
            <button className="btn btn-primary" onClick={onOpenAddModal}>
              <Plus size={16} />
              <span>Add Vehicle</span>
            </button>
          </div>
        </div>

        {loading && vehicles.length === 0 ? (
          <Spinner label="Loading fleet data..." />
        ) : vehicles.length === 0 ? (
          <div className="empty-state">
            <Car className="empty-state-icon" />
            <h3>No vehicles in fleet</h3>
            <p>Add a vehicle to begin monitoring. A Docker container will be started automatically.</p>
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Vehicle ID</th>
                <th>Owner</th>
                <th>Model</th>
                <th>Health</th>
                <th>Container</th>
                <th>Container ID</th>
                <th>Added</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {vehicles.map(vehicle => (
                <tr key={vehicle.id}>
                  <td>
                    <div className="cell-id">
                      <Car size={16} style={{ color: 'var(--color-text-tertiary)' }} />
                      #{vehicle.id}
                    </div>
                  </td>
                  <td>{vehicle.owner || '—'}</td>
                  <td>{vehicle.model || '—'}</td>
                  <td><StatusBadge status={vehicle.status} /></td>
                  <td>
                    <span className={`container-badge ${containerBadgeClass(vehicle.containerStatus)}`}>
                      {vehicle.containerStatus || 'PENDING'}
                    </span>
                  </td>
                  <td className="cell-mono">{formatContainerId(vehicle.containerId)}</td>
                  <td>{formatDate(vehicle.createdAt)}</td>
                  <td className="cell-actions">
                    <button
                      className="btn btn-danger"
                      onClick={() => setDeleteTarget(vehicle.id)}
                      title="Remove vehicle"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmDialog
        isOpen={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Remove Vehicle"
        message={`This will permanently remove Vehicle #${deleteTarget} and destroy its Docker container. This action cannot be undone.`}
        confirmLabel="Remove Vehicle"
        loading={deleting}
      />
    </>
  );
};

export default FleetTable;
