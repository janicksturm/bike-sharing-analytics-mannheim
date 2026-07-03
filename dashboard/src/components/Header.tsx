import { NavLink } from "react-router-dom";

function Header() {
  const linkBase = "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2";
  const linkActive = "bg-emerald-600/15 text-emerald-400";
  const linkInactive = "text-gray-400 hover:text-white hover:bg-gray-700/50";

  return (
    <header className="sticky bg-gray-800">
      <div className="pb-10 pt-10 max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-white">
            Nextbike Mannheim
          </span>
          <span className="text-xl uppercase tracking-widest text-emerald-600">
            Station Analytics Dashboard
          </span>
        </div>

        <nav className="flex items-center gap-1 bg-gray-900 rounded-xl p-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `${linkBase} ${isActive ? linkActive : linkInactive}`
            }
          >
            Status
          </NavLink>

          <NavLink
            to="/prediction"
            className={({ isActive }) =>
              `${linkBase} ${isActive ? linkActive : linkInactive}`
            }
          >
            Prediction
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

export default Header;