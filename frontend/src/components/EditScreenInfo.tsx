import React from 'react';

interface EditScreenInfoProps {
    path: string;
}

export default function EditScreenInfo({ path }: EditScreenInfoProps) {
    return (
        <div className="text-center px-4">
            <div className="mb-6">
                <p className="text-gray-800 dark:text-gray-200 text-lg leading-6">
                    Open up the code for this screen:
                </p>

                <div className="my-2 bg-black/5 dark:bg-white/10 rounded px-2 py-1 inline-block">
                    <code className="text-sm font-mono text-blue-600 dark:text-blue-400">{path}</code>
                </div>

                <p className="text-gray-800 dark:text-gray-200 text-lg leading-6 mt-2">
                    Change any of the text, save the file, and your app will automatically update.
                </p>
            </div>

            <div className="mt-4">
                <a
                    href="https://docs.expo.io/get-started/create-a-new-app/#opening-the-app-on-your-phonetablet"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 dark:text-blue-400 underline hover:text-blue-800"
                >
                    Tap here if your app doesn't automatically update after making changes
                </a>
            </div>
        </div>
    );
}
