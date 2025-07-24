export async function getCompanies(): Promise<any[]> {
  return [
    {
      id: 1,
      name: "Company 1",
    },
    {
      id: 2,
      name: "Company 2",
    },
    {
      id: 3,
      name: "Company 3",
    },
    {
      id: 4,
      name: "Company 4",
    },
  ];
}

export async function createCompany(name: string): Promise<any> {
  return {
    id: 1,
    name: name,
  };
}

export async function updateCompany(id: number, name: string): Promise<any> {
  return {
    id: id,
    name: name,
  };
}

export async function deleteCompany(id: number): Promise<void> {
  return;
}
