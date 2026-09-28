import React, { useState } from 'react';
import TopBar from '../components/layout/TopBar';
import FleetTable from '../components/fleet/FleetTable';
import AddVehicleModal from '../components/fleet/AddVehicleModal';

const FleetPage = ({ vehicles, loading, onRefresh }) => {
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <>
      <TopBar title="Fleet Management" />
      <div className="page-content">
        <FleetTable
          vehicles={vehicles}
          loading={loading}
          onRefresh={onRefresh}
          onOpenAddModal={() => setShowAddModal(true)}
        />

        <AddVehicleModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          onSuccess={onRefresh}
        />
      </div>
    </>
  );
};

export default FleetPage;
