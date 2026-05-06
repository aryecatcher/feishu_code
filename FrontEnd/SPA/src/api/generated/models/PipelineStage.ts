/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AgentConfig } from './AgentConfig';
import type { StageType } from './StageType';
/**
 * A single stage in the pipeline.
 */
export type PipelineStage = {
    /**
     * Unique stage identifier
     */
    id: string;
    /**
     * Stage display name
     */
    name: string;
    /**
     * Stage type
     */
    stage_type: StageType;
    /**
     * Stage description
     */
    description: string;
    /**
     * Agent configuration
     */
    agent: AgentConfig;
    /**
     * Whether this stage requires human approval
     */
    is_checkpoint?: boolean;
    /**
     * Stage IDs this stage depends on
     */
    depends_on?: Array<string>;
    /**
     * Stage-specific configuration
     */
    config?: Record<string, any>;
};

