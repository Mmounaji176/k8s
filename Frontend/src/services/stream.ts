import useAxios from "./axios";

export async function getStreams(
  companyId?: number,
  zoneId?: number
): Promise<any[]> {
  const axios = useAxios()
  return axios.get("/api/stream/");
}

export async function getStream(id: number): Promise<any> {
  
}

export async function createStream(
  companyId: number,
  zoneId: number,
  title: string,
  url: string
): Promise<any> {
  const axios = useAxios()
  return  axios.post("/api/stream/",{title:title,url:url,place:zoneId});
}

export async function deleteStream(id: number): Promise<void> {
  return;
}
