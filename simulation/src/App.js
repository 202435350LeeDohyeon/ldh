import "mapbox-gl/dist/mapbox-gl.css";
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

import Splash from "./components/Splash";
import Trip from "./components/Trip";
import "./css/app.css";

const fetchData = (FilE_NAME) => {
  const res = axios.get(
    // 자신의 깃허브 주소 입력
    // https://raw.githubusercontent.com/'자신 깃허브 이름'/simulation/main/simulation/src/data/${FilE_NAME}.json
    `https://raw.githubusercontent.com/HNU209/simulation-class/main/simulation/src/data/${FilE_NAME}.json`
  );
  const data = res.then((r) => r.data);
  return data;
};

const App = () => {

  const [trip, setTrip] = useState([]);

  const [isloaded, setIsLoaded] = useState(false);
  
  const getData = useCallback(async () => {
    const TRIP = await fetchData("trips");

    setTrip((prev) => TRIP);

    setIsLoaded(true);
  }, []);

  useEffect(() => {
    getData();
  }, [getData]);

  return (
    <div className="container">
      {!isloaded && <Splash />}
      {isloaded && (
        <Trip trip={trip} />
      )}
    </div>
  );
};

export default App;
