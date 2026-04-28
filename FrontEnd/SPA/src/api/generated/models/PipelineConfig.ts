/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type PipelineConfig = {
    /**
     * 用于绑定模板，可采用默认值
     */
    pipeline_id: number;
    /**
     * 文字描述该模板
     */
    descriptions: {
        title: string;
        content?: string;
    };
    /**
     * 连接各阶段StageID
     */
    stages: Array<number>;
    config?: any;
};

