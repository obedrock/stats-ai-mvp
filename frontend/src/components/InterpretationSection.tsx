import { Card, CardContent } from "@/components/ui/card";

interface InterpretationSectionProps {
  text: string;
}

export function InterpretationSection({ text }: InterpretationSectionProps) {
  return (
    <section id="interpretation">
      <Card className="bg-slate-800 border-slate-700">
        <CardContent className="pt-6">
          <h2 className="text-[20px] font-semibold leading-[1.2] text-foreground mb-4">
            Interpretation
          </h2>
          <div className="text-sm text-foreground leading-relaxed whitespace-pre-line">
            {text}
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
