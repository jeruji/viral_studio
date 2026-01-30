

import React from "react";
import { Routes, Route } from "react-router-dom";
import Login from "./users/LoginPage"
import HomePage from "./jobs/HomePage"
import ListJobs from "./jobs/listJobs";


const Loading = () => <p>Loading...</p>;

const App = () => {
  return (
    <>
      <div className="min-vh-100 bg-white" style={{ overflowY: "hidden" }}>
        <React.Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route path="/login" element={<Login />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/list-jobs" element={<ListJobs />} />
          </Routes>
        </React.Suspense>
      </div>
    </>
  );
};

export default App;
