function Header() {
  return (
    <header className="sticky bg-gray-800">
      <div className="pb-10 flex flex-col pl-6 pt-10 ml-50">
        <span className="text-xs font-semibold text-white">
            Nextbike Mannheim
        </span>
        <span className="text-xl uppercase tracking-widest text-emerald-600">
            Station Analytics Dashboard
        </span>
      </div>
    </header>
  );
}

export default Header;