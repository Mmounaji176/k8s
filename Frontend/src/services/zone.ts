export async function getZones(companyId: string) {
  return [
    {
      id: 1,
      name: "Zone 1",
    },
    {
      id: 2,
      name: "Zone 2",
    },
    {
      id: 3,
      name: "Zone 3",
    },
    {
      id: 4,
      name: "Zone 4",
    },
  ];
}

export async function createZone(companyId: string, name: string) {
  return {
    id: 1,
    name: name,
  };
}

export async function updateZone(zoneId: string, name: string) {
  return {
    id: zoneId,
    name: name,
  };
}

export async function deleteZone(zoneId: string) {
  return;
}
