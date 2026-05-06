/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Agent configuration for a stage.
 */
export type AgentConfig = {
    /**
     * Agent name
     */
    name: string;
    /**
     * System prompt for the agent
     */
    system_prompt?: string;
    temperature?: number;
    max_tokens?: number;
    /**
     * Available tools
     */
    tools?: Array<string>;
};

