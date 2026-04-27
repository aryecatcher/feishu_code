/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Checkpoint = {
    /**
     * 连接运行实例
     */
    run_id: number;
    /**
     * 标注检查点
     */
    checkpoint_id: number;
    /**
     * 呈现检查点内容
     */
    reviews: string;
    resolution: {
        /**
         * accept|reject
         */
        action: string;
        /**
         * 反馈内容编号
         */
        context_id: number;
    };
};

