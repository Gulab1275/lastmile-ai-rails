"use client";

import React, { createContext, useContext, useEffect, useState } from "react";

export type Language = "ur" | "en";

interface UIContextValue {
  lang: Language;
  setLang: (l: Language) => void;
  toggleLang: () => void;
  lowBandwidth: boolean;
  setLowBandwidth: (b: boolean) => void;
  toggleLowBandwidth: () => void;
  t: (ur: string, en: string) => string;
}

const UIContext = createContext<UIContextValue>({
  lang: "ur",
  setLang: () => {},
  toggleLang: () => {},
  lowBandwidth: false,
  setLowBandwidth: () => {},
  toggleLowBandwidth: () => {},
  t: (ur) => ur,
});

export function UIProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Language>("ur");
  const [lowBandwidth, setLowBandwidthState] = useState<boolean>(false);

  useEffect(() => {
    try {
      const savedLang = localStorage.getItem("rahbar_lang") as Language | null;
      if (savedLang === "ur" || savedLang === "en") {
        setLangState(savedLang);
        document.documentElement.lang = savedLang;
        document.documentElement.dir = savedLang === "ur" ? "rtl" : "ltr";
      } else {
        document.documentElement.lang = "ur";
        document.documentElement.dir = "rtl";
      }

      const savedLB = localStorage.getItem("rahbar_low_bandwidth");
      if (savedLB === "true") {
        setLowBandwidthState(true);
        document.documentElement.classList.add("low-bandwidth");
      }
    } catch {
      // LocalStorage access fallback
    }
  }, []);

  const setLang = (newLang: Language) => {
    setLangState(newLang);
    try {
      localStorage.setItem("rahbar_lang", newLang);
      document.documentElement.lang = newLang;
      document.documentElement.dir = newLang === "ur" ? "rtl" : "ltr";
    } catch {
      // Safe fallback
    }
  };

  const toggleLang = () => {
    setLang(lang === "ur" ? "en" : "ur");
  };

  const setLowBandwidth = (lb: boolean) => {
    setLowBandwidthState(lb);
    try {
      localStorage.setItem("rahbar_low_bandwidth", lb ? "true" : "false");
      if (lb) {
        document.documentElement.classList.add("low-bandwidth");
      } else {
        document.documentElement.classList.remove("low-bandwidth");
      }
    } catch {
      // Safe fallback
    }
  };

  const toggleLowBandwidth = () => {
    setLowBandwidth(!lowBandwidth);
  };

  const t = (ur: string, en: string) => (lang === "ur" ? ur : en);

  return (
    <UIContext.Provider
      value={{
        lang,
        setLang,
        toggleLang,
        lowBandwidth,
        setLowBandwidth,
        toggleLowBandwidth,
        t,
      }}
    >
      {children}
    </UIContext.Provider>
  );
}

export function useUI() {
  return useContext(UIContext);
}
