// FaceAnalyticsPage.jsx
import { FaceAnalytics } from './components/FaceAnalytics';
import { useEffect, useState } from 'react';
import useAxios from '../../services/axios';

export const FaceAnalyticsPage = ({ id }) => {
  const [faceStats, setFaceStats] = useState(null);
  const axios = useAxios();

  useEffect(() => {
    const fetchFaceStats = async () => {
      try {
        const response = !id
          ? await axios.get("/faceanalyzer/face_stats")
          : await axios.get(`/faceanalyzer/face_stats/${id}`);
        setFaceStats(response.data);
      } catch (error) {
        console.error("Error fetching face stats:", error);
      }
    };
    fetchFaceStats();
  }, [axios, id]); // Added missing dependencies

  return <FaceAnalytics faceStats={faceStats} />;
};
