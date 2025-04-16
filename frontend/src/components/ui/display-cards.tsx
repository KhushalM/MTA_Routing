"use client";

import { cn } from "@/lib/utils";
import { Sparkles } from "lucide-react";
import React, { useState } from "react";

interface DisplayCardProps {
  className?: string;
  icon?: React.ReactNode;
  title?: string;
  description?: string;
  date?: string;
  iconClassName?: string;
  titleClassName?: string;
  style?: React.CSSProperties;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
  isHovered?: boolean;
  zIndex?: number;
}

function DisplayCard({
  className,
  icon = <Sparkles className="size-4 text-blue-300" />,
  title = "Featured",
  description = "Discover amazing content",
  iconClassName = "text-blue-500",
  titleClassName = "text-blue-500",
  style = {},
  onMouseEnter,
  onMouseLeave,
  isHovered = false,
  zIndex = 1,
}: DisplayCardProps) {
  return (
    <div
      className={cn(
        "relative flex h-36 w-full sm:w-[22rem] select-none flex-col justify-between rounded-xl border-2 bg-muted/70 backdrop-blur-sm px-4 py-3 transition-all duration-300 shadow-lg cursor-pointer",
        isHovered && "z-50 scale-105 shadow-2xl",
        className
      )}
      style={{ ...style, zIndex }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div>
        <span className={cn("relative inline-block rounded-full bg-blue-800 p-1", iconClassName)}>
          {icon}
        </span>
        <p className={cn("text-lg font-medium", titleClassName)}>{title}</p>
      </div>
      <p className="text-base text-foreground/80 leading-snug">{description}</p>
    </div>
  );
}

interface DisplayCardsProps {
  cards?: DisplayCardProps[];
}

// Diagonal offsets for a centered stack
const DIAGONAL_XY = [
  { x: 0, y: 0 },
  { x: 50, y: 50 },
  { x: 100, y: 100 },
  { x: 150, y: 150 },
  { x: 250, y: 200 },
  { x: 350, y: 250 },
];
const ROTATION = [0, 0, 0, 0, 0, 0];

export default function DisplayCards({ cards }: DisplayCardsProps) {
  const displayCards = cards || [];
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <div className="relative min-h-[400px] flex items-center justify-center py-10" style={{ perspective: '1000px' }}>
      {displayCards.map((cardProps, index) => {
        // Center the diagonal stack
        const centerX = '50%';
        const centerY = '50%';
        const offset = DIAGONAL_XY[index % DIAGONAL_XY.length];
        const isHovered = hovered === index;
        return (
          <DisplayCard
            key={index}
            {...cardProps}
            style={{
              position: 'absolute',
              left: `calc(${centerX} + ${offset.x}px - 11rem)`, // 11rem is half card width
              top: `calc(${centerY} + ${offset.y}px - 4.5rem)`, // 4.5rem is half card height
              transform: isHovered
                ? `translate(-50%, -50%) translateY(-40px) scale(1.08) rotate(${ROTATION[index % ROTATION.length]}deg)`
                : `translate(-50%, -50%) rotate(${ROTATION[index % ROTATION.length]}deg)`,
              width: '22rem',
              maxWidth: '90vw',
              transition: 'all 0.3s cubic-bezier(.4,2,.6,1)',
            }}
            zIndex={isHovered ? 99 : index}
            isHovered={isHovered}
            onMouseEnter={() => setHovered(index)}
            onMouseLeave={() => setHovered(null)}
          />
        );
      })}
    </div>
  );
}