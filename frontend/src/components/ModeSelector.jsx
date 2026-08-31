import { AI_MODES } from "../constants/modes";


function ModeSelector({
  selectedMode,
  onModeChange,
}) {

  return (
    <select
      value={selectedMode}
      onChange={(event) =>
        onModeChange(
          event.target.value
        )
      }
      className="rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-200 outline-none focus:border-blue-500"
    >

      {AI_MODES.map((mode) => (

        <option
          key={mode.id}
          value={mode.id}
        >
          {mode.icon} {mode.label}
        </option>

      ))}

    </select>
  );
}


export default ModeSelector;