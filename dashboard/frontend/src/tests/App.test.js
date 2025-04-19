import { render, screen } from '@testing-library/react';
import App from '../App';
import { Provider } from 'react-redux';
import { store } from '../store';

// Mock des dépendances
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  BrowserRouter: ({ children }) => <div>{children}</div>,
}));

jest.mock('../views/Overview', () => () => <div>Overview Page</div>);
jest.mock('../views/Login', () => () => <div>Login Page</div>);
jest.mock('../layouts/MainLayout', () => ({ children }) => <div>Main Layout{children}</div>);

describe('App Component', () => {
  it('renders without crashing', () => {
    render(
      <Provider store={store}>
        <App />
      </Provider>
    );
  });
});
