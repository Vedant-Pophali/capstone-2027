#!/usr/bin/env python3
"""
factory_enrollment.py — Offline CRP Database Seeding Script

Simulates the factory provisioning phase described in the research paper.
For each vehicle, this script:
  1. Instantiates a VehiclePUF (using pypuf ArbiterPUF or the fallback).
  2. Generates N random challenge seeds.
  3. Evaluates the PUF response for each challenge.
  4. Derives the response hash (same formula as CryptographicSigner.derive_session_key).
  5. POSTs a batch of CRPs to the fleet-manager /api/puf/ota-renew endpoint,
     which stores them in the embedded SQLite database.

Usage:
    python factory_enrollment.py --vehicle-ids 1,2,3 --count 10000
    python factory_enrollment.py --vehicle-ids 42   --count 5000 --endpoint http://localhost:8081

Constraints:
    - Does NOT touch src/ml.
    - Safe to run multiple times (CRPs are additive — old ones are not overwritten).
"""

import argparse
import hashlib
import json
import random
import sys
import urllib.request
import numpy as np
import os


# ─────────────────────────────────────────────────────────────────────────────
# Utility: Derive response hash (mirrors CryptographicSigner.derive_session_key)
# ─────────────────────────────────────────────────────────────────────────────

def derive_response_hash(puf_response: np.ndarray) -> str:
    """SHA-256 of the packed PUF response bits — this is what the cloud stores."""
    response_bytes = np.packbits((puf_response > 0).astype(int)).tobytes()
    return hashlib.sha256(response_bytes).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Enrollment logic for a single vehicle
# ─────────────────────────────────────────────────────────────────────────────

def enroll_vehicle(vehicle_id: str, count: int, endpoint: str) -> int:
    """
    Generate `count` CRPs for the given vehicle and POST them to the fleet-manager.
    Returns the number of CRPs successfully stored.
    """
    print(f"\n[Factory] Enrolling vehicle {vehicle_id} with {count} CRPs...")

    # Set VEHICLE_ID so the VehiclePUF seeds itself correctly
    os.environ["VEHICLE_ID"] = str(vehicle_id)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from edge_vehicles.src.security.puf_simulator import VehiclePUF
    puf = VehiclePUF()

    crp_batch = []
    for i in range(count):
        seed = random.randint(10_000, 9_999_999)
        try:
            _, response = puf.get_response(seed)
            response_hash = derive_response_hash(response)
            crp_batch.append({
                "challenge": str(seed),
                "responseHash": response_hash
            })
        except Exception as e:
            print(f"[Factory] Warning: skipped seed {seed} due to error: {e}")

        if (i + 1) % 1000 == 0:
            print(f"[Factory]   ... {i + 1}/{count} CRPs generated")

    print(f"[Factory] Generated {len(crp_batch)} CRPs. Uploading to fleet-manager...")

    # POST to the OTA renewal endpoint (reused for initial enrollment too)
    url = f"{endpoint.rstrip('/')}/api/puf/ota-renew"
    payload = json.dumps({
        "vehicleId": str(vehicle_id),
        "crpBatch": crp_batch
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            stored = result.get("stored", 0)
            print(f"[Factory] ✓ Vehicle {vehicle_id}: {stored} CRPs stored in SQLite.")
            return stored
    except Exception as e:
        print(f"[Factory] ✗ Failed to upload CRPs for vehicle {vehicle_id}: {e}")
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PUF Factory Enrollment Script")
    parser.add_argument("--vehicle-ids", type=str, default="42",
                        help="Comma-separated list of vehicle IDs (e.g. 1,2,3)")
    parser.add_argument("--count", type=int, default=10_000,
                        help="Number of CRPs to generate per vehicle (default: 10000)")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8081",
                        help="fleet-manager base URL (default: http://localhost:8081)")
    args = parser.parse_args()

    vehicle_ids = [vid.strip() for vid in args.vehicle_ids.split(",")]
    total_stored = 0

    print("=" * 60)
    print("  PUF Factory Enrollment — Offline CRP Provisioning")
    print("=" * 60)
    print(f"  Vehicles  : {vehicle_ids}")
    print(f"  CRPs/veh  : {args.count:,}")
    print(f"  Endpoint  : {args.endpoint}")
    print("=" * 60)

    for vid in vehicle_ids:
        total_stored += enroll_vehicle(vid, args.count, args.endpoint)

    print(f"\n[Factory] Enrollment complete. Total CRPs stored: {total_stored:,}")


if __name__ == "__main__":
    main()
