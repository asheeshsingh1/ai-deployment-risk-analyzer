import type { ReactNode } from "react";

interface PageContainerProps {
    children: ReactNode;
}

function PageContainer({ children }: PageContainerProps) {
    return <main className="page-container">{children}</main>;
}

export default PageContainer;