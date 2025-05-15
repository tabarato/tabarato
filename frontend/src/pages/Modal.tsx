import React from 'react';
import EditScreenInfo from '../components/EditScreenInfo';

export default function ModalScreen() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-white dark:bg-gray-900">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Modal</h1>
            <div className="my-8 h-px w-4/5 bg-gray-200 dark:bg-white/10" />
            <EditScreenInfo path="app/modal.tsx" />
        </div>
    );
}
