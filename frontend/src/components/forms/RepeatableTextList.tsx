import { Textarea } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";

interface RepeatableTextListProps {
  label: string;
  items: string[];
  onChange: (items: string[]) => void;
  placeholder?: string;
  addLabel?: string;
  minItems?: number;
  rows?: number;
}

/** Lista editable de strings (parrafos, puntos clave, etc.) con agregar/quitar. */
export function RepeatableTextList({
  label,
  items,
  onChange,
  placeholder,
  addLabel = "Agregar",
  minItems = 0,
  rows = 2,
}: RepeatableTextListProps) {
  const update = (index: number, value: string) => {
    const next = [...items];
    next[index] = value;
    onChange(next);
  };

  const remove = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  const add = () => {
    onChange([...items, ""]);
  };

  return (
    <div>
      <span className="label">{label}</span>
      <div className="mt-1 space-y-2">
        {items.map((item, index) => (
          <div key={index} className="flex gap-2">
            <Textarea
              rows={rows}
              value={item}
              placeholder={placeholder}
              onChange={(e) => update(index, e.target.value)}
              className="flex-1"
            />
            <button
              type="button"
              onClick={() => remove(index)}
              disabled={items.length <= minItems}
              aria-label="Quitar"
              className="focus-ring h-fit rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-40 dark:hover:bg-red-900/30"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
      </div>
      <Button type="button" variant="ghost" size="sm" className="mt-2" onClick={add}>
        + {addLabel}
      </Button>
    </div>
  );
}
