import React from "react";
import { OverlayTrigger, Tooltip } from "react-bootstrap";
import { useNavigate } from "react-router-dom";

export default function NavbarPage() {
  const navigate = useNavigate();

  const logOut = () => {
    localStorage.removeItem("user");
    navigate("/login");
  };

  const menuItems = [
    {
      title: "Home",
      icon: "/images/Home-icon.svg",
      action: () => {
        navigate("/home");
        navigate(0);
      },
    },
    {
      title: "List Jobs",
      icon: "/images/clipboard-list.svg",
      action: () => navigate("/list-jobs"),
    },
    {
      title: "List User",
      icon: "/images/icon-user-blue.svg",
      action: () => navigate("/list-user"),
    },
  ];

  return (
    <>
      <div className="d-none d-lg-block">
        <div
          className="left-sidebar vh-100 position-fixed shadow-lg"
          style={{ backgroundColor: "#ffffff", width: "80px" }}
        >
          <div
            className="sidebar-logo text-center d-flex align-items-center justify-content-center"
            onClick={() => navigate("/home")}
          >
            <img
              src={"/images/gdp-logo-white.svg"}
              className="cursor-pointer"
              style={{ height: "40px" }}
            />
          </div>

          <div className="d-flex flex-column align-items-center mt-5 gap-4">
            {menuItems.map((item, idx) => (
              <OverlayTrigger
                key={idx}
                placement="right"
                delay={{ show: 50, hide: 0 }}
                overlay={
                  <Tooltip style={{ position: "fixed" }}>{item.title}</Tooltip>
                }
              >
                <img
                  className="cursor-pointer menu-icon"
                  src={item.icon}
                  onClick={item.action}
                />
              </OverlayTrigger>
            ))}
          </div>

          <div className="container-fluid position-absolute bottom-0 d-flex justify-content-center mb-3">
            <OverlayTrigger
              placement="right"
              delay={{ show: 50, hide: 0 }}
              overlay={<Tooltip style={{ position: "fixed" }}>Log out</Tooltip>}
            >
              <img
                className="cursor-pointer menu-icon"
                src={"/images/logout-icon.svg"}
                style={{ width: "25px" }}
                onClick={logOut}
              />
            </OverlayTrigger>
          </div>
        </div>
      </div>
      {/* Topbar versi mobile */}
      <div className="d-lg-none bg-white d-flex align-items-center shadow-sm">
        <div
          className="cursor-pointer sidebar-logo p-2"
          onClick={() => navigate("/home")}
          style={{ flex: "0 0 auto" }}
        >
          <img
            src="/images/gdp-logo-white.svg"
            alt="Logo"
            style={{ height: "45px", objectFit: "contain" }}
          />
        </div>

        <div
          className="d-flex justify-content-center gap-4 flex-grow-1"
          style={{ textAlign: "center" }}
        >
          {menuItems.map((item, itemIndex) => {
            return (
              <img
                className="cursor-pointer menu-icon"
                src={item.icon}
                onClick={item.action}
                key={`mobile-${itemIndex}`}
                alt="Home"
                style={{ height: "26px" }}
              />
            )
          })}
        </div>

        <div style={{ flex: "0 0 auto" }}>
          <img
            className="cursor-pointer menu-icon"
            src="/images/logout-icon.svg"
            alt="Logout"
            style={{ width: "26px" }}
            onClick={logOut}
          />
        </div>
      </div>
    </>
  );
}
