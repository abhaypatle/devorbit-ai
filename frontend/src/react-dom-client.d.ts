declare module 'react-dom/client' {
  const ReactDOM: {
    createRoot(container: Element | DocumentFragment): {
      render(children: unknown): void;
    };
  };

  export default ReactDOM;
}