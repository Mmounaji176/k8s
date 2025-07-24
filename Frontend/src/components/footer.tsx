export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <div className="flex justify-center items-center h-24 w-full">
      Bluedove {currentYear}.
    </div>
  );
}
