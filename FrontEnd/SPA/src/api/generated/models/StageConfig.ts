/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type StageConfig = {
    stage_id: number;
    /**
     * 简要描述阶段内容
     */
    descriptions: {
        title: string;
        content?: string;
    };
    /**
     * 配置该阶段Agent信息
     */
    agent_config: {
        /**
         * 提供大模型接入
         */
        model_provider: any;
        /**
         * 配置预定信息
         */
        roles: any;
    };
};

