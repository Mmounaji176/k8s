import { SVGProps } from "react";

export type IconSvgProps = SVGProps<SVGSVGElement> & {
  size?: number;
};

export type HTMLElementEvent<T extends HTMLElement> = Event & {
  target: T;
};

export type STREAM_TYPE = {
  title: string;
  url: string;
  thumbnail?: string;
  index: number;
};

export type STATUS = {
  usage: number;
  unit: string;
  label: string;
  percentage?: number;
};
