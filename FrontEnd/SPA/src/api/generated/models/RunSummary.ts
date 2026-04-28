/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RunSummary = {
    /**
     * 连接流水线模板
     */
    pipeline_id: number;
    /**
     * 标注实例
     */
    run_id: number;
    summary: {
        /**
         * running|paused|awaiting_checkpoint|completed|failed|cancelled
         */
        status: string;
        /**
         * 连接stage_id
         */
        current_stage: string;
    };
};

