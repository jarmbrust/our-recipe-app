import { defineConfig, globalIgnores } from "eslint/config";
import nextPlugin from "@next/eslint-plugin-next";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";
import globals from "globals";

/**
 * Custom ESLint 10 flat config.
 *
 * Replaces eslint-config-next with its directly-compatible building blocks so the
 * project can run on ESLint 10 now. The three plugins that do not yet declare
 * ESLint 10 support (eslint-plugin-react, eslint-plugin-jsx-a11y,
 * eslint-plugin-import) are intentionally omitted — see docs/recommendations.md
 * for the re-add checklist.
 */
const eslintConfig = defineConfig([
    {
        name: "next/core-web-vitals",
        files: ["**/*.{js,jsx,mjs,ts,tsx,mts,cts}"],
        ...nextPlugin.configs["core-web-vitals"],
    },
    {
        name: "react-hooks/recommended",
        files: ["**/*.{js,jsx,mjs,ts,tsx,mts,cts}"],
        ...reactHooks.configs.flat.recommended,
    },
    ...tseslint.configs.recommended,
    {
        name: "globals/browser-node",
        languageOptions: {
            globals: {
                ...globals.browser,
                ...globals.node,
            },
        },
    },
    globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);

export default eslintConfig;
